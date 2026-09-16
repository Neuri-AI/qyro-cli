"""
Filesystem, settings and template adapters.

The global mutable SETTINGS dict is now reached through SettingsRepository, so
use cases depend on an interface they can fake instead of on module state.
"""

import shutil
import getpass
import json
from getpass import getuser
from os import listdir, mkdir, remove, unlink
from os.path import dirname, exists, isdir, isfile, islink, join
from pathlib import Path
from shutil import rmtree
from string import Template
from typing import Dict, List

from qyro.domain.errors import MissingSettingError
from qyro.domain.project import ComponentSpec, ProjectConfig

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

    def make_dir(self, path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def write_text(self, path: str, content: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def read_file(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def copy_tree(self, source: str, destination: Path) -> None:
        shutil.copytree(
            source,
            destination,
            dirs_exist_ok=True,
        )

    def remove_dir(self, path: str) -> None:
        shutil.rmtree(path, ignore_errors=True)

    def default_author(self) -> str:
        try:
            return getpass.getuser()
        except Exception:
            return "Unknown"

    def render_tree(
        self,
        root: str,
        variables: dict[str, object],
        exclude: set[str] | None = None,
    ) -> None:
        root_path = Path(root)
        excluded = exclude or set()

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

    @property
    def base_settings_path(self) -> str:
        return BASE_SETTINGS

    def get(self, key: str):
        from qyro import SETTINGS
        try:
            return SETTINGS[key]
        except KeyError:
            raise MissingSettingError(key) from None

    def get_optional(self, key: str, default=None):
        from qyro import SETTINGS
        return SETTINGS.get(key, default)

    def set(self, key: str, value) -> None:
        from qyro import SETTINGS
        SETTINGS[key] = value

    def activate_profile(self, profile: str) -> None:
        from qyro import activate_profile
        activate_profile(profile)

    def persist_base(self, values: Dict[str, object]) -> None:
        from qyro import path
        from qyro.builtin_commands._util import update_json
        update_json(path(BASE_SETTINGS), values)


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
