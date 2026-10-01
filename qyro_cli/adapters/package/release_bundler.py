"""
qyro.adapters.package.release_bundler
Filesystem implementation of BundlePort.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from qyro_cli.application.ports import BundlePort
from qyro_cli.domain.build import BundleArtifact
from qyro_cli.domain.errors import (
    FrozenAppNotFoundError,
    MissingDependencyError,
    QyroError,
    UnsupportedOperationError,
)


class ReleaseBundler(BundlePort):
    """Copy frozen artifacts into a release layout and optionally archive it."""

    def preflight(
        self,
        *,
        project_root: Path,
        app_name: str,
        freeze_dir: str,
        package_format: str,
        target_platform: str,
        extra_files: list[object],
        dmg_options: dict[str, object],
    ) -> None:
        freeze_root = project_root / freeze_dir
        if not freeze_root.exists():
            raise FrozenAppNotFoundError(str(freeze_root))

        self._validate_extra_files(
            project_root=project_root,
            extra_files=extra_files,
        )

        platform_name = self._resolve_platform(target_platform)
        resolved_format = self._resolve_format(platform_name, package_format)

        if resolved_format == "dmg":
            if platform_name != "mac":
                raise UnsupportedOperationError("bundle:dmg", platform_name)
            self._validate_dmg_requirements(
                project_root=project_root,
                app_name=app_name,
                freeze_root=freeze_root,
                dmg_options=dmg_options,
            )
            return

        if resolved_format == "nsis":
            if platform_name != "windows":
                raise UnsupportedOperationError("bundle:nsis", platform_name)
            if shutil.which("makensis") is None:
                raise MissingDependencyError("makensis")
            return

        if resolved_format in ("deb", "rpm", "arch"):
            if platform_name != "linux":
                raise UnsupportedOperationError(f"bundle:{resolved_format}", platform_name)
            if shutil.which("fpm") is None:
                raise MissingDependencyError("fpm")
            return

    def bundle(
        self,
        *,
        project_root: Path,
        app_name: str,
        freeze_dir: str,
        release_dir: str,
        include_resources: bool,
        create_archive: bool,
        package_format: str,
        target_platform: str,
        app_version: str,
        extra_files: list[object],
        dmg_options: dict[str, object],
    ) -> BundleArtifact:
        freeze_root = project_root / freeze_dir
        if not freeze_root.exists():
            raise FrozenAppNotFoundError(str(freeze_root))

        output_root = project_root / release_dir / app_name
        if output_root.exists():
            shutil.rmtree(output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        included_paths: list[Path] = []

        for source in self._resolve_artifact_sources(freeze_root, app_name):
            if source.is_dir() and source.name == app_name:
                # Keep release/<app>/... for onedir output instead of nesting twice.
                for child in source.iterdir():
                    destination = output_root / child.name
                    self._copy_path(child, destination)
                    included_paths.append(destination)
            else:
                destination = output_root / source.name
                self._copy_path(source, destination)
                included_paths.append(destination)

        if include_resources:
            resources_dir = project_root / "resources"
            if resources_dir.exists() and resources_dir.is_dir():
                destination = output_root / "resources"
                shutil.copytree(resources_dir, destination, dirs_exist_ok=True)
                included_paths.append(destination)

        included_paths.extend(
            self._copy_extra_files(
                project_root=project_root,
                output_root=output_root,
                extra_files=extra_files,
            )
        )

        archive_path: Path | None = None
        if create_archive:
            archive_base = (project_root / release_dir) / app_name
            archive_file = shutil.make_archive(
                str(archive_base),
                "zip",
                root_dir=output_root,
            )
            archive_path = Path(archive_file)

        resolved_platform = self._resolve_platform(target_platform)
        resolved_format = self._resolve_format(resolved_platform, package_format)

        package_path: Path | None = None
        if resolved_format != "dir":
            package_path = self._build_platform_package(
                output_root=output_root,
                release_root=project_root / release_dir,
                app_name=app_name,
                app_version=app_version,
                platform_name=resolved_platform,
                package_format=resolved_format,
                project_root=project_root,
                dmg_options=dmg_options,
            )

        return BundleArtifact(
            output_dir=output_root,
            included_paths=included_paths,
            archive_path=archive_path,
            package_path=package_path,
            package_format=(None if resolved_format == "dir" else resolved_format),
        )

    def _resolve_artifact_sources(self, freeze_root: Path, app_name: str) -> list[Path]:
        candidates = [
            freeze_root / f"{app_name}.app",
            freeze_root / app_name,
            freeze_root / f"{app_name}.exe",
            freeze_root / app_name,
        ]

        result: list[Path] = []
        for candidate in candidates:
            if candidate.exists() and candidate not in result:
                result.append(candidate)

        if not result:
            raise FrozenAppNotFoundError(str(freeze_root / app_name))

        return result

    def _copy_path(self, source: Path, destination: Path) -> None:
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    def _resolve_platform(self, target_platform: str) -> str:
        platform_value = (target_platform or "auto").lower()
        if platform_value in ("mac", "windows", "linux"):
            return platform_value

        if sys.platform.startswith("darwin"):
            return "mac"
        if sys.platform.startswith("win"):
            return "windows"
        return "linux"

    def _resolve_format(self, platform_name: str, package_format: str) -> str:
        fmt = (package_format or "auto").lower()
        if fmt != "auto":
            return fmt

        if platform_name == "mac":
            return "dmg"
        if platform_name == "windows":
            return "nsis"
        return "tar.gz"

    def _build_platform_package(
        self,
        *,
        output_root: Path,
        release_root: Path,
        app_name: str,
        app_version: str,
        platform_name: str,
        package_format: str,
        project_root: Path,
        dmg_options: dict[str, object],
    ) -> Path:
        if package_format == "zip":
            archive_base = release_root / f"{app_name}-{app_version}"
            return Path(
                shutil.make_archive(str(archive_base), "zip", root_dir=output_root)
            )

        if package_format == "tar.gz":
            archive_base = release_root / f"{app_name}-{app_version}"
            return Path(
                shutil.make_archive(str(archive_base), "gztar", root_dir=output_root)
            )

        if package_format == "dmg":
            if platform_name != "mac":
                raise UnsupportedOperationError("bundle:dmg", platform_name)
            return self._package_dmg(
                output_root,
                release_root,
                app_name,
                app_version,
                project_root=project_root,
                dmg_options=dmg_options,
            )

        if package_format == "nsis":
            if platform_name != "windows":
                raise UnsupportedOperationError("bundle:nsis", platform_name)
            return self._package_nsis(output_root, release_root, app_name, app_version)

        if package_format in ("deb", "rpm", "arch"):
            if platform_name != "linux":
                raise UnsupportedOperationError(f"bundle:{package_format}", platform_name)
            return self._package_linux_fpm(
                output_root=output_root,
                release_root=release_root,
                app_name=app_name,
                app_version=app_version,
                package_format=package_format,
            )

        raise UnsupportedOperationError(f"bundle:{package_format}", platform_name)

    def _package_dmg(
        self,
        output_root: Path,
        release_root: Path,
        app_name: str,
        app_version: str,
        *,
        project_root: Path,
        dmg_options: dict[str, object],
    ) -> Path:
        app_bundle = output_root / f"{app_name}.app"
        if not app_bundle.exists():
            raise FrozenAppNotFoundError(str(app_bundle))

        dmg_path = release_root / f"{app_name}-{app_version}.dmg"
        if dmg_path.exists():
            dmg_path.unlink()

        dmg_source_dir = release_root / f".{app_name}-dmg-src"
        if dmg_source_dir.exists():
            shutil.rmtree(dmg_source_dir)
        dmg_source_dir.mkdir(parents=True, exist_ok=True)
        staged_app_bundle = dmg_source_dir / app_bundle.name
        shutil.copytree(app_bundle, staged_app_bundle)

        has_custom_options = self._has_dmg_customizations(dmg_options)

        try:
            # Prefer create-dmg for a better UX installer presentation.
            if shutil.which("create-dmg") is not None:
                command = [
                    "create-dmg",
                    "--volname",
                    app_name,
                ]

                window_pos = self._extract_xy(dmg_options.get("window"))
                if window_pos is not None:
                    command.extend([
                        "--window-pos",
                        str(window_pos[0]),
                        str(window_pos[1]),
                    ])

                window_size = self._extract_wh(dmg_options.get("window_size"))
                if window_size is not None:
                    command.extend([
                        "--window-size",
                        str(window_size[0]),
                        str(window_size[1]),
                    ])

                icon_size = dmg_options.get("icon_size")
                if isinstance(icon_size, int) and icon_size > 0:
                    command.extend(["--icon-size", str(icon_size)])

                app_pos = self._extract_xy(
                    dmg_options.get("app_position")
                    or dmg_options.get("app_icon_position")
                )
                if app_pos is not None:
                    command.extend([
                        "--icon",
                        app_bundle.name,
                        str(app_pos[0]),
                        str(app_pos[1]),
                    ])

                applications_pos = self._extract_xy(
                    dmg_options.get("applications_position")
                    or dmg_options.get("app_drop_link")
                )
                if applications_pos is not None:
                    command.extend([
                        "--app-drop-link",
                        str(applications_pos[0]),
                        str(applications_pos[1]),
                    ])

                background_path = self._resolve_optional_path(
                    dmg_options.get("background"),
                    project_root,
                    required=has_custom_options,
                )
                if background_path is not None:
                    command.extend(["--background", str(background_path)])

                command.extend([
                    str(dmg_path),
                    str(dmg_source_dir),
                ])
                try:
                    self._run(command, cwd=str(release_root))
                    return dmg_path
                except RuntimeError:
                    # If custom options were requested, failing here must be explicit.
                    if has_custom_options:
                        raise

            if has_custom_options:
                raise QyroError(
                    "create-dmg is required to apply DMG customization options from release settings.",
                    hint=(
                        "Install create-dmg with one of these commands:\n"
                        "  brew install create-dmg\n"
                        "  npm install -g create-dmg\n"
                        "Or remove bundle.dmg custom options from build/settings/release.json."
                    ),
                )

            if shutil.which("hdiutil") is None:
                raise QyroError(
                    "Could not create DMG because hdiutil is not available.",
                    hint="Use macOS host tools or install create-dmg.",
                )

            applications_link = dmg_source_dir / "Applications"
            if applications_link.exists() or applications_link.is_symlink():
                applications_link.unlink()
            applications_link.symlink_to("/Applications")

            hdiutil_command = [
                "hdiutil",
                "create",
                "-volname",
                app_name,
                "-srcfolder",
                str(dmg_source_dir),
                "-ov",
                "-format",
                "UDZO",
                str(dmg_path),
            ]
            self._run(hdiutil_command, cwd=str(release_root))
            return dmg_path
        finally:
            if dmg_source_dir.exists():
                shutil.rmtree(dmg_source_dir, ignore_errors=True)

    def _has_dmg_customizations(self, options: dict[str, object]) -> bool:
        if not options:
            return False
        keys = {
            "window",
            "window_size",
            "icon_size",
            "app_position",
            "app_icon_position",
            "applications_position",
            "app_drop_link",
            "background",
        }
        return any(k in options for k in keys)

    def _validate_dmg_requirements(
        self,
        *,
        project_root: Path,
        app_name: str,
        freeze_root: Path,
        dmg_options: dict[str, object],
    ) -> None:
        app_bundle = freeze_root / f"{app_name}.app"
        if not app_bundle.exists():
            raise FrozenAppNotFoundError(str(app_bundle))

        has_custom_options = self._has_dmg_customizations(dmg_options)
        if has_custom_options and shutil.which("create-dmg") is None:
            raise QyroError(
                "create-dmg is required to apply DMG customization options from release settings.",
                hint=(
                    "Install create-dmg with one of these commands:\n"
                    "  brew install create-dmg\n"
                    "  npm install -g create-dmg\n"
                    "Or remove bundle.dmg custom options from build/settings/release.json."
                ),
            )

        self._resolve_optional_path(
            dmg_options.get("background"),
            project_root,
            required=has_custom_options,
        )

    def _validate_extra_files(
        self,
        *,
        project_root: Path,
        extra_files: list[object],
    ) -> None:
        for item in extra_files:
            source_value: str | None = None
            destination_value: str | None = None

            if isinstance(item, str):
                source_value = item
            elif isinstance(item, dict):
                source_raw = item.get("source")
                if isinstance(source_raw, str):
                    source_value = source_raw
                destination_raw = item.get("destination")
                if isinstance(destination_raw, str):
                    destination_value = destination_raw

            if not source_value:
                continue

            source_path = self._resolve_path(source_value, project_root)
            if not source_path.exists():
                raise FileNotFoundError(f"Extra bundle file was not found: {source_path}")

            if destination_value:
                destination_relative = Path(destination_value)
                if destination_relative.is_absolute():
                    raise ValueError(
                        f"Extra bundle destination must be relative: {destination_relative}"
                    )

    def _copy_extra_files(
        self,
        *,
        project_root: Path,
        output_root: Path,
        extra_files: list[object],
    ) -> list[Path]:
        copied: list[Path] = []

        for item in extra_files:
            source_value: str | None = None
            destination_value: str | None = None

            if isinstance(item, str):
                source_value = item
            elif isinstance(item, dict):
                source_raw = item.get("source")
                if isinstance(source_raw, str):
                    source_value = source_raw
                destination_raw = item.get("destination")
                if isinstance(destination_raw, str):
                    destination_value = destination_raw

            if not source_value:
                continue

            source_path = self._resolve_path(source_value, project_root)
            if not source_path.exists():
                raise FileNotFoundError(f"Extra bundle file was not found: {source_path}")

            if destination_value:
                destination_relative = Path(destination_value)
            else:
                destination_relative = Path(source_path.name)

            if destination_relative.is_absolute():
                raise ValueError(
                    f"Extra bundle destination must be relative: {destination_relative}"
                )

            destination_path = (output_root / destination_relative).resolve()
            output_root_resolved = output_root.resolve()
            if output_root_resolved not in destination_path.parents and destination_path != output_root_resolved:
                raise ValueError(
                    f"Extra bundle destination escapes output directory: {destination_relative}"
                )

            self._copy_path(source_path, destination_path)
            copied.append(destination_path)

        return copied

    def _resolve_path(self, value: str, project_root: Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (project_root / path).resolve()

    def _resolve_optional_path(
        self,
        value: object,
        project_root: Path,
        *,
        required: bool = False,
    ) -> Path | None:
        if not isinstance(value, str) or not value.strip():
            return None
        candidate = self._resolve_path(value.strip(), project_root)
        if not candidate.exists():
            if required:
                raise FileNotFoundError(
                    f"Configured path does not exist: {candidate}"
                )
            return None
        return candidate

    def _extract_xy(self, raw: object) -> tuple[int, int] | None:
        if not isinstance(raw, dict):
            return None
        x = raw.get("x")
        y = raw.get("y")
        if isinstance(x, int) and isinstance(y, int):
            return x, y
        return None

    def _extract_wh(self, raw: object) -> tuple[int, int] | None:
        if not isinstance(raw, dict):
            return None
        width = raw.get("width")
        height = raw.get("height")
        if isinstance(width, int) and isinstance(height, int):
            return width, height
        return None

    def _package_nsis(
        self,
        output_root: Path,
        release_root: Path,
        app_name: str,
        app_version: str,
    ) -> Path:
        if shutil.which("makensis") is None:
            raise MissingDependencyError("makensis")

        installer_path = release_root / f"{app_name}-{app_version}-setup.exe"
        nsi_path = release_root / f"{app_name}-installer.nsi"
        nsis_output = str(installer_path).replace("/", "\\")
        source_dir = str(output_root).replace("/", "\\")

        nsi_content = (
            'OutFile "' + nsis_output + '"\n'
            'Name "' + app_name + '"\n'
            'InstallDir "$PROGRAMFILES\\' + app_name + '"\n'
            'RequestExecutionLevel user\n'
            'Page directory\n'
            'Page instfiles\n\n'
            'Section "Install"\n'
            '  SetOutPath "$INSTDIR"\n'
            '  File /r "' + source_dir + '\\*"\n'
            'SectionEnd\n'
        )

        nsi_path.write_text(nsi_content, encoding="utf-8")
        self._run(["makensis", str(nsi_path)], cwd=str(release_root))
        return installer_path

    def _package_linux_fpm(
        self,
        *,
        output_root: Path,
        release_root: Path,
        app_name: str,
        app_version: str,
        package_format: str,
    ) -> Path:
        if shutil.which("fpm") is None:
            raise MissingDependencyError("fpm")

        fpm_target = "pacman" if package_format == "arch" else package_format
        extension = {
            "deb": "deb",
            "rpm": "rpm",
            "arch": "pkg.tar.zst",
        }[package_format]

        package_path = release_root / f"{app_name}-{app_version}.{extension}"
        command = [
            "fpm",
            "-s",
            "dir",
            "-t",
            fpm_target,
            "-n",
            app_name,
            "-v",
            app_version,
            "-C",
            str(output_root),
            "--prefix",
            f"/opt/{app_name}",
            "-p",
            str(package_path),
            ".",
        ]
        self._run(command, cwd=str(release_root))
        return package_path

    def _run(self, command: list[str], cwd: str) -> None:
        completed = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Packaging command failed: "
                + " ".join(command)
                + "\n"
                + (completed.stdout or "")
            )
