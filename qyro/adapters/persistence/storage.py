"""
Filesystem, settings and template adapters.

The global mutable SETTINGS dict is now reached through SettingsRepository, so
use cases depend on an interface they can fake instead of on module state.
"""

import shutil
import json
import getpass
from pathlib import Path
from string import Template
from typing import Dict, Sequence

from qyro.domain.errors import MissingSettingError
from qyro.domain.project import ComponentSpec

BASE_SETTINGS = "settings/base.json"
TEXT_EXTENSIONS = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


class OsFileSystem:
    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def is_dir(self, path: str) -> bool:
        return Path(path).is_dir()

    def resolve(self, relative_path: str) -> str:
        return str(Path(relative_path).resolve())

    def make_directory(self, relative_path: str) -> None:
        Path(relative_path).mkdir(parents=True, exist_ok=True)

    def remove_tree(self, relative_path: str) -> None:
        shutil.rmtree(relative_path, ignore_errors=True)

    def empty_directory(self, relative_path: str) -> None:
        directory = Path(relative_path)

        if not directory.exists():
            return

        for path in directory.iterdir():
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)

    def write_text(
        self,
        relative_path: str,
        content: str,
    ) -> None:
        target = Path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def read_text(self, relative_path: str) -> str:
        return Path(relative_path).read_text(encoding="utf-8")

    def copy_tree(
        self,
        source: Path,
        destination: Path,
    ) -> None:
        shutil.copytree(
            source,
            destination,
            dirs_exist_ok=True,
        )

    def current_user(self) -> str:
        try:
            return getpass.getuser()
        except Exception:
            return "Unknown"

    def render_tree(
        self,
        root: str,
        variables: dict[str, object],
        exclude: Sequence[str] | None = None,
    ) -> None:
        root_path = Path(root)
        excluded = set(exclude or ())

        for path in root_path.rglob("*"):
            if not path.is_file():
                continue

            if str(path.relative_to(root_path)) in excluded:
                continue

            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue

            content = path.read_text(encoding="utf-8")
            rendered = Template(content).substitute(variables)

            path.write_text(
                rendered,
                encoding="utf-8",
            )

class SettingsRepository:
    """
    SettingsPort over ppg's SETTINGS dict.

    `get` raises a typed domain error instead of a bare KeyError, so use cases
    never have to catch KeyError and guess what it meant.
    """


class SettingsRepository:
    def __init__(self, project_root: Path = None):
        self._root = project_root or Path.cwd()
        self._settings = self._load_base()

    @property
    def base_settings_path(self) -> str:
        return str(self._root / BASE_SETTINGS)

    def _load_base(self) -> dict:
        path = self._root / BASE_SETTINGS

        if not path.exists():
            return {}

        return json.loads(path.read_text(encoding="utf-8"))

    def get(self, key: str):
        try:
            return self._settings[key]
        except KeyError:
            raise MissingSettingError(key) from None

    def get_optional(self, key: str, default=None):
        return self._settings.get(key, default)

    def set(self, key: str, value) -> None:
        self._settings[key] = value

    def activate_profile(self, profile: str) -> None:
        profile_path = self._root / "settings" / f"{profile}.json"

        if not profile_path.exists():
            return

        profile_settings = json.loads(
            profile_path.read_text(encoding="utf-8")
        )

        self._settings.update(profile_settings)

    def persist_base(self, values: Dict[str, object]) -> None:
        path = self._root / BASE_SETTINGS
        settings = self._load_base()
        settings.update(values)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(settings, indent=4),
            encoding="utf-8",
        )




class ComponentFileWriter:
    """ComponentWriterPort: renders and writes a component/view file."""

    def __init__(self, project_root: Path = None):
        self._root = project_root or Path.cwd()

    def _directory(self, spec: ComponentSpec) -> Path:
        return (self._root / "src" / "main" / "python"
                / spec.type.directory_name)

    def target_path(self, spec: ComponentSpec) -> str:
        return str(self._directory(spec) / spec.file_name)

    def target_exists(self, spec: ComponentSpec) -> bool:
        return Path(self.target_path(spec)).exists()

    def render(self, spec: ComponentSpec) -> str:
        from qyro.builtin_commands.components import component_template
        return Template(component_template).substitute(
            **spec.template_variables()
        )

    def write(self, spec: ComponentSpec, code: str) -> str:
        directory = self._directory(spec)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / spec.file_name).write_text(code, encoding="utf-8")
        return str(directory)
