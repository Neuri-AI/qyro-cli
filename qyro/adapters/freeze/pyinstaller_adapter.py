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
from qyro.domain.errors import QyroError


class FreezeExecutionError(QyroError):
    """Raised when PyInstaller returns a non-zero exit code."""

    def __init__(self, command: str, exit_code: int, output: str):
        super().__init__(
            f"Freezing failed with exit code {exit_code}.",
            hint=f"Check PyInstaller logs below:\n{output[-1500:] if len(output) > 1500 else output}",
        )
        self.command = command
        self.exit_code = exit_code
        self.output = output


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

        # Bundle mode (onedir vs onefile)
        if manifest.bundle_mode == BundleMode.ONEFILE:
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")

        # Debug & Console
        if manifest.debug.console_window or manifest.debug.enabled:
            cmd.append("--console")
        else:
            cmd.append("--windowed")  # GUI app: no terminal popup

        if manifest.debug.bootloader_debug:
            cmd.append("--debug=all")
        elif manifest.debug.unstripped:
            cmd.append("--debug=imports")

        # Windows UAC elevation
        if manifest.target_platform == "windows" and manifest.uac.requires_admin:
            cmd.append("--uac-admin")
        if manifest.target_platform == "windows" and manifest.uac.ui_access:
            cmd.append("--uac-uiaccess")

        # Icon
        if manifest.icon_path:
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

        if not manifest.optimization.upx_enabled:
            cmd.append("--noupx")
        else:
            for upx_exc in manifest.optimization.upx_excludes:
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
