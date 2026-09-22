"""
qyro.adapters.freeze.pyinstaller_adapter
PyInstaller-based freezer implementing FreezerPort.
Constructs arguments, creates Windows UAC manifests, handles debug/onefile/onedir modes,
runs the PyInstaller process cleanly, and captures output artifacts.
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from qyro.application.ports import (
    FreezerPort,
    FrameworkHookResolverPort,
    ProgressPort,
    UserInteractionPort,
)
from qyro.domain.build import (
    BuildArtifact,
    BundleMode,
    FreezeManifest,
    UACLevel,
)
from qyro.domain.errors import QyroError, FreezeExecutionError


class PyInstallerFreezer(FreezerPort):
    """Clean Architecture adapter wrapping PyInstaller executable."""

    def __init__(
        self,
        resolver: FrameworkHookResolverPort,
        ui: Optional[UserInteractionPort] = None,
        progress: Optional[ProgressPort] = None,
    ):
        self._resolver = resolver
        self._ui = ui
        self._progress = progress

    def freeze(
        self,
        project_root: Path,
        manifest: FreezeManifest,
        extra_args: Optional[List[str]] = None,
    ) -> BuildArtifact:
        start_time = time.time()

        # Build PyInstaller command list
        cmd = [sys.executable, "-m", "PyInstaller"]

        # Target script
        entry_script = project_root / manifest.entry_point
        if not entry_script.exists():
            raise QyroError(
                f"Entry point '{manifest.entry_point}' not found in '{project_root}'",
                hint="Verify 'entry_point' in settings/base.json or build.json.",
            )

        cmd.append(str(entry_script))

        # Application Name
        cmd.extend(["--name", manifest.app_name])

        # Distpath & Workpath inside 'build/' (Qyro convention)
        build_dir = project_root / "build"
        dist_dir = build_dir
        build_work_dir = build_dir / "temp"
        spec_dir = build_dir

        cmd.extend(["--distpath", str(dist_dir)])
        cmd.extend(["--workpath", str(build_work_dir)])
        cmd.extend(["--specpath", str(spec_dir)])

        is_mac_target = manifest.target_platform.lower() in ("mac", "macos", "darwin") or (
            manifest.target_platform == "auto" and sys.platform == "darwin"
        )

        # Bundle mode (onedir vs onefile)
        if manifest.bundle_mode == BundleMode.ONEFILE:
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")

        # Debug & Console
        is_console_mode = manifest.debug.console_window or manifest.debug.enabled
        if is_console_mode:
            cmd.append("--console")
        else:
            cmd.append("--windowed")  # GUI app: no terminal popup

        if is_mac_target and not is_console_mode and "--windowed" not in cmd and "-w" not in cmd:
            cmd.append("-w")  # Force generation of .app bundle on macOS for windowed GUI apps

        if manifest.debug.bootloader_debug:
            cmd.append("--debug=all")
        elif manifest.debug.unstripped:
            cmd.append("--debug=imports")

        # Windows UAC elevation
        if manifest.target_platform == "windows" and manifest.uac.requires_admin:
            cmd.append("--uac-admin")
        if manifest.target_platform == "windows" and manifest.uac.ui_access:
            cmd.append("--uac-uiaccess")

        # macOS Bundle Identifier
        if is_mac_target:
            bundle_id = manifest.mac_bundle_identifier or manifest.suggest_bundle_id()
            if bundle_id:
                cmd.extend(["--osx-bundle-identifier", bundle_id])

        # Icon handling
        if is_mac_target:
            icns_file = self._handle_mac_icon(project_root, dist_dir, manifest)
            if icns_file and icns_file.exists():
                cmd.extend(["--icon", str(icns_file)])
        elif manifest.icon_path:
            icon_file = project_root / manifest.icon_path
            if icon_file.exists():
                cmd.extend(["--icon", str(icon_file)])

        # Hidden imports from manifest
        for hi in manifest.hidden_imports:
            cmd.extend(["--hidden-import", hi])

        # Framework-specific hooks (Qt, Kivy, Tkinter, resources)
        framework_args = self._resolver.resolve_args(project_root, manifest)
        cmd.extend(framework_args)

        # Optimization configurations
        if manifest.optimization.clean_build:
            cmd.append("--clean")

        if is_mac_target or not manifest.optimization.upx_enabled:
            cmd.append("--noupx")
        else:
            for upx_exc in manifest.optimization.upx_excludes:
                exc_lower = upx_exc.lower()
                target_p = manifest.target_platform.lower()
                # Smart OS filter: discard incompatible binary extensions
                if target_p == "linux":
                    if exc_lower.endswith(".dll") or exc_lower.endswith(".pyd"):
                        continue
                elif target_p == "windows":
                    if exc_lower.endswith(".so") or ".so." in exc_lower or exc_lower.endswith(".dylib"):
                        continue
                cmd.extend(["--upx-exclude", upx_exc])

        # Module exclusions for lightweight binaries
        for exc_mod in manifest.optimization.exclude_modules:
            cmd.extend(["--exclude-module", exc_mod])

        # Extra PyInstaller arguments
        if manifest.extra_pyinstaller_args:
            cmd.extend(manifest.extra_pyinstaller_args)
        if extra_args:
            cmd.extend(extra_args)

        cmd.append("-y")  # Overwrite output directory without prompting

        if self._progress:
            self._progress.start(f"Freezing '{manifest.app_name}' with {manifest.binding}...")
        elif self._ui:
            self._ui.progress(f"Freezing '{manifest.app_name}' [{manifest.bundle_mode.value}]...")

        # Run PyInstaller subprocess
        env = dict(os.environ)
        existing_py_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(project_root) + os.pathsep + existing_py_path
            if existing_py_path
            else str(project_root)
        )

        # Bytecode optimization flag
        if manifest.optimization.bytecode_opt > 0:
            env["PYTHONOPTIMIZE"] = str(manifest.optimization.bytecode_opt)

        process = subprocess.run(
            cmd,
            cwd=str(project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if self._progress:
            self._progress.stop()

        if process.returncode != 0:
            raise FreezeExecutionError(
                command=" ".join(cmd),
                exit_code=process.returncode,
                output=process.stdout,
            )

        duration = time.time() - start_time

        # Cleanup temporary build files and any leftover empty nested directories
        if manifest.optimization.clean_build and build_work_dir.exists():
            shutil.rmtree(build_work_dir, ignore_errors=True)

        leftover_nested_build = build_dir / "build"
        if leftover_nested_build.exists() and leftover_nested_build.is_dir():
            shutil.rmtree(leftover_nested_build, ignore_errors=True)

        # Post-process for macOS app bundle
        if is_mac_target:
            app_bundle = dist_dir / f"{manifest.app_name}.app"
            if app_bundle.exists():
                self._remove_unwanted_pyinstaller_files(app_bundle)
                self._copy_mac_resources(project_root, app_bundle)
                self._purge_excluded_binaries(app_bundle, manifest)

        # Calculate output executable path and size
        if manifest.bundle_mode == BundleMode.ONEFILE:
            ext = ".exe" if manifest.target_platform == "windows" else ""
            out_exe = dist_dir / f"{manifest.app_name}{ext}"
            out_folder = dist_dir
            size = out_exe.stat().st_size if out_exe.exists() else 0
        else:
            out_folder = dist_dir / manifest.app_name
            ext = ".exe" if manifest.target_platform == "windows" else ""
            out_exe = out_folder / f"{manifest.app_name}{ext}"
            if is_mac_target and (dist_dir / f"{manifest.app_name}.app").exists():
                out_folder = dist_dir / f"{manifest.app_name}.app"
                out_exe = out_folder / "Contents" / "MacOS" / manifest.app_name
            self._purge_excluded_binaries(out_folder, manifest)
            size = self._calc_dir_size(out_folder)

        return BuildArtifact(
            output_dir=out_folder,
            executable_path=out_exe,
            bundle_mode=manifest.bundle_mode,
            size_bytes=size,
            duration_seconds=duration,
            manifest_used=manifest,
            uac_applied=manifest.uac.requires_admin,
            debug_mode=manifest.debug.enabled,
            binding=manifest.binding,
        )

    def _calc_dir_size(self, path: Path) -> int:
        if not path.exists():
            return 0
        if path.is_file():
            return path.stat().st_size
        total = 0
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total

    def _handle_mac_icon(
        self,
        project_root: Path,
        target_dir: Path,
        manifest: FreezeManifest,
    ) -> Optional[Path]:
        """Auto-generates target/Icon.icns from source icon using iconutil if needed."""
        if manifest.icon_path:
            icon_p = project_root / manifest.icon_path
            if icon_p.exists() and icon_p.suffix.lower() == ".icns":
                return icon_p

        icns_path = target_dir / "Icon.icns"
        if icns_path.exists():
            return icns_path

        candidates = [
            project_root / "resources" / "mac" / "icons" / "1024.png",
            project_root / "resources" / "mac" / "icon.png",
            project_root / "resources" / "base" / "icons" / "icon.png",
            project_root / "resources" / "base" / "icon.png",
            project_root / "resources" / "icon.png",
            project_root / "icon.png",
        ]

        source_icon = next((c for c in candidates if c.exists()), None)
        if not source_icon:
            return None

        iconset_dir = target_dir / "Icon.iconset"
        iconset_dir.mkdir(parents=True, exist_ok=True)
        sizes = [
            (16, 1), (16, 2),
            (32, 1), (32, 2),
            (128, 1), (128, 2),
            (256, 1), (256, 2),
            (512, 1), (512, 2),
        ]

        try:
            from PIL import Image
            img = Image.open(source_icon)
            for size, scale in sizes:
                px = size * scale
                dest_name = f"icon_{size}x{size}"
                if scale != 1:
                    dest_name += f"@{scale}x"
                dest_name += ".png"
                resized = img.resize((px, px), Image.Resampling.LANCZOS)
                resized.save(iconset_dir / dest_name)
        except Exception:
            for size, scale in sizes:
                dest_name = f"icon_{size}x{size}"
                if scale != 1:
                    dest_name += f"@{scale}x"
                dest_name += ".png"
                shutil.copy(source_icon, iconset_dir / dest_name)

        try:
            subprocess.run(
                ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return icns_path
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def _remove_unwanted_pyinstaller_files(self, app_bundle: Path) -> None:
        """Removes unwanted folders like include, lib, lib2to3 inside Contents/Resources."""
        contents_res = app_bundle / "Contents" / "Resources"
        if not contents_res.exists():
            return

        for unwanted in ("include", "lib", "lib2to3"):
            target = contents_res / unwanted
            if target.exists() or target.is_symlink():
                try:
                    if target.is_dir() and not target.is_symlink():
                        shutil.rmtree(target, ignore_errors=True)
                    else:
                        os.unlink(target)
                except OSError:
                    pass

    def _copy_mac_resources(self, project_root: Path, app_bundle: Path) -> None:
        """Copies resources to Contents/Resources inside the .app bundle."""
        res_dest = app_bundle / "Contents" / "Resources"
        res_dest.mkdir(parents=True, exist_ok=True)

        resource_sources = [
            project_root / "resources",
            project_root / "src" / "main" / "resources",
            project_root / "src" / "freeze",
        ]

        for src_dir in resource_sources:
            if src_dir.exists() and src_dir.is_dir():
                for item in src_dir.iterdir():
                    dest = res_dest / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)

    def _purge_excluded_binaries(self, output_dir: Path, manifest: FreezeManifest) -> None:
        """Purges C++ frameworks, shared objects (.so), DLLs, dylibs, and binary plugins for modules listed in exclude_modules."""
        if not output_dir.exists():
            return

        exclude_modules = set(manifest.optimization.exclude_modules or [])

        # Extract lowercase keywords for matching (e.g. 'virtualkeyboard', 'webengine', 'pdf', 'qml', 'quick')
        keywords: set[str] = set()
        exact_targets: set[str] = set()

        for exc in exclude_modules:
            parts = exc.split(".")
            short_name = parts[-1]  # e.g., QtWebEngineCore, Qt3DCore, QtQuick, QtQml, QtVirtualKeyboard
            qt_suffix = short_name[2:] if short_name.startswith("Qt") and len(short_name) > 2 else short_name

            kw = qt_suffix.lower()
            if kw:
                keywords.add(kw)
            if short_name.lower():
                keywords.add(short_name.lower())

            # Specific exact targets
            exact_targets.update([
                f"{short_name}.framework".lower(),
                f"{short_name}.abi3.so".lower(),
                f"{short_name}.so".lower(),
                f"{short_name}.pyd".lower(),
                f"{short_name}.dylib".lower(),
                f"{short_name}.dll".lower(),
            ])

        # Walk bottom-up to safely delete files and subdirectories
        for root, dirs, files in os.walk(str(output_dir), topdown=False):
            # Check files and symlinks
            for f in files:
                file_p = Path(root) / f
                f_lower = f.lower()

                should_delete = False
                if f_lower in exact_targets:
                    should_delete = True
                else:
                    for kw in keywords:
                        if kw in f_lower:
                            should_delete = True
                            break

                if should_delete:
                    try:
                        if file_p.is_symlink() or file_p.is_file():
                            os.unlink(file_p)
                        elif file_p.is_dir():
                            shutil.rmtree(file_p, ignore_errors=True)
                    except OSError:
                        pass

            # Check directory names
            for d in dirs:
                dir_p = Path(root) / d
                d_lower = d.lower()

                should_delete = False
                for kw in keywords:
                    if kw in d_lower:
                        should_delete = True
                        break

                if should_delete:
                    try:
                        if dir_p.is_symlink():
                            os.unlink(dir_p)
                        elif dir_p.is_dir():
                            shutil.rmtree(dir_p, ignore_errors=True)
                    except OSError:
                        pass

        # Perform Qt asset optimization cleanups if clean_build is enabled
        if manifest.optimization.clean_build:
            for qt_binding in ("PySide6", "PyQt6", "PySide2", "PyQt5"):
                for qt_path in list(output_dir.rglob(f"{qt_binding}/Qt")) + list(output_dir.rglob(f"{qt_binding}/Qt6")):
                    if not qt_path.exists() or not qt_path.is_dir():
                        continue

                    # 1. Purge translations folder (hundreds of .qm files saving 25MB+)
                    trans_dir = qt_path / "translations"
                    if trans_dir.exists() and trans_dir.is_dir():
                        shutil.rmtree(trans_dir, ignore_errors=True)

                    # 2. Purge qml folder if QML is excluded
                    if any("qml" in k or "quick" in k for k in keywords):
                        qml_dir = qt_path / "qml"
                        if qml_dir.exists() and qml_dir.is_dir():
                            shutil.rmtree(qml_dir, ignore_errors=True)

                    # 3. Purge unused heavyweight plugins (egldeviceintegrations, wayland-*)
                    plugins_dir = qt_path / "plugins"
                    if plugins_dir.exists() and plugins_dir.is_dir():
                        for plug_name in (
                            "egldeviceintegrations",
                            "wayland-decoration-client",
                            "wayland-graphics-integration-client",
                            "wayland-shell-integration",
                        ):
                            plug_p = plugins_dir / plug_name
                            if plug_p.exists():
                                shutil.rmtree(plug_p, ignore_errors=True)

        # Cleanup Pass: Purge any broken symlinks remaining anywhere in output_dir
        for root, dirs, files in os.walk(str(output_dir), topdown=False):
            for name in files + dirs:
                p = Path(root) / name
                if p.is_symlink() and not p.exists():
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

