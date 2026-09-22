
"""
qyro.adapters.freeze.framework_hooks
Framework-specific resolution hooks for Qyro's Freeze system.
Handles PyQt5, PyQt6, PySide2, PySide6, Kivy, Tkinter hidden imports and resource data,
integrating with Qyro's domain Binding and Project entities.
"""

from pathlib import Path
from typing import Callable, List

from qyro.application.ports import FrameworkHookResolverPort
from qyro.domain.build import FreezeManifest
from qyro.domain.project import Binding, AddonModule


class FrameworkHookResolver(FrameworkHookResolverPort):
    """
    Intelligently inspects project files and domain Binding to resolve:
    - PyInstaller hidden imports
    - Collect data / resource paths
    - Binary dependencies (SDL2, GLEW, etc. for Kivy)
    - Plugin directories for Qt family
    - Common project settings and assets
    """

    def resolve_args(
        self,
        project_root: Path,
        manifest: FreezeManifest,
    ) -> List[str]:
        args: List[str] = []

        binding = Binding.parse(manifest.binding)

        resolvers: dict[Binding, Callable[[Path, FreezeManifest], List[str]]] = {
            Binding.PYSIDE6: self._resolve_pyside6,
            Binding.PYQT6: self._resolve_pyqt6,
            Binding.PYQT5: self._resolve_pyqt5,
            Binding.PYSIDE2: self._resolve_pyside2,
            Binding.KIVY: self._resolve_kivy,
            Binding.TKINTER: self._resolve_tkinter,
        }

        resolver = resolvers.get(binding)

        if resolver:
            args.extend(resolver(project_root, manifest))

        args.extend(self._resolve_addons(manifest))
        args.extend(self._resolve_project_assets(project_root, manifest))

        return args

    def _resolve_qt(
        self,
        package: str,
        *,
        sip: bool = False,
    ) -> List[str]:
        args = [
            "--hidden-import", package,
            "--hidden-import", f"{package}.QtCore",
            "--hidden-import", f"{package}.QtGui",
            "--hidden-import", f"{package}.QtWidgets",
        ]

        if package == "PySide6":
            args.extend(["--exclude-module", "PySide6.scripts"])

        if package == "PySide2":
            args.extend(["--exclude-module", "PySide2.scripts"])

        if package == "PyQt6":
            args.extend(["--exclude-module", "PyQt6.scripts"])

        if package == "PyQt5":
            args.extend(["--exclude-module", "PyQt5.scripts"])

        if sip:
            args.extend(["--hidden-import", f"{package}.sip"])

        return args

    def _resolve_pyside6(
        self,
        project_root: Path,
        manifest: FreezeManifest,
    ) -> List[str]:
        args = self._resolve_qt("PySide6")

        # Check for QML / Quick in project
        if self._has_qml(project_root):
            args.extend([
                "--hidden-import", "PySide6.QtQuick",
                "--hidden-import", "PySide6.QtQml",
            ])

        return args

    def _resolve_pyqt6(
        self,
        project_root: Path,
        manifest: FreezeManifest,
    ) -> List[str]:
        return self._resolve_qt("PyQt6", sip=True)

    def _resolve_pyqt5(
        self,
        project_root: Path,
        manifest: FreezeManifest,
    ) -> List[str]:
        return self._resolve_qt("PyQt5", sip=True)

    def _resolve_pyside2(
        self,
        project_root: Path,
        manifest: FreezeManifest,
    ) -> List[str]:
        return self._resolve_qt("PySide2")

    def _resolve_kivy(
        self,
        project_root: Path,
        manifest: FreezeManifest,
    ) -> List[str]:
        args = [
            "--hidden-import", "kivy",
            "--hidden-import", "kivy.core.window.window_sdl2",
            "--hidden-import", "kivy.core.text.text_sdl2",
            "--hidden-import", "kivy.core.image.img_sdl2",
            "--hidden-import", "kivy.core.clipboard.clipboard_sdl2",
            "--hidden-import", "kivy.graphics.cgl_backend.cgl_glew",
            "--collect-submodules", "kivy",
            "--collect-data", "kivy",
        ]

        # Scan and bundle .kv files (Kivy declarative layout files)
        kv_patterns = [
            "*.kv",
            "views/**/*.kv",
            "components/**/*.kv",
        ]

        collected_kv: set[str] = set()

        for pattern in kv_patterns:
            for path in project_root.glob(pattern):
                if not path.is_file():
                    continue

                relative = path.relative_to(project_root)
                source = path.resolve().as_posix()
                destination = relative.parent.as_posix()

                if destination == ".":
                    destination = "."

                collected_kv.add(
                    f"{source}{self._data_separator(manifest)}{destination}"
                )

        for item in sorted(collected_kv):
            args.extend(["--add-data", item])

        return args

    def _resolve_tkinter(
        self,
        project_root: Path,
        manifest: FreezeManifest,
    ) -> List[str]:
        return [
            "--hidden-import", "tkinter",
            "--hidden-import", "tkinter.ttk",
            "--hidden-import", "tkinter.messagebox",
            "--hidden-import", "tkinter.filedialog",
            "--collect-data", "tkinter",
        ]

    def _resolve_addons(
        self,
        manifest: FreezeManifest,
    ) -> List[str]:
        """Resolves PyInstaller args for registered addons."""
        args: List[str] = []
        addons = {str(addon).lower() for addon in (manifest.addons or [])}

        if AddonModule.REQUESTS.value.lower() in addons:
            args.extend([
                "--hidden-import", "requests",
                "--hidden-import", "urllib3",
                "--hidden-import", "certifi",
                "--collect-data", "certifi",
            ])

        if "kivymd" in addons:
            args.extend([
                "--hidden-import", "kivymd",
                "--collect-submodules", "kivymd",
                "--collect-data", "kivymd",
            ])

        if "plyer" in addons:
            args.extend([
                "--hidden-import", "plyer",
                "--collect-submodules", "plyer",
            ])

        return args

    def _resolve_project_assets(
        self,
        project_root: Path,
        manifest: FreezeManifest,
    ) -> List[str]:
        args: List[str] = []

        resources_dir_name = manifest.resources_dir or "resources"
        resources_path = (project_root / resources_dir_name).resolve()

        if resources_path.is_dir():
            args.extend([
                "--add-data",
                f"{resources_path.as_posix()}{self._data_separator(manifest)}{resources_dir_name}",
            ])

        settings_path = (project_root / "settings").resolve()
        if settings_path.is_dir():
            args.extend([
                "--add-data",
                f"{settings_path.as_posix()}{self._data_separator(manifest)}settings",
            ])

        return args

    def _data_separator(self, manifest: FreezeManifest) -> str:
        return ";" if manifest.target_platform == "windows" else ":"

    def _has_qml(self, project_root: Path) -> bool:
        return any(project_root.rglob("*.qml"))
