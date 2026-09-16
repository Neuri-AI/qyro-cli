
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from qyro.adapters.persistence.storage import (
    ComponentFileWriter,
    OsFileSystem,
    SettingsRepository,
)
from qyro.domain.errors import MissingSettingError


class TestOsFileSystem:
    def test_exists(self, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("hello")

        fs = OsFileSystem()

        assert fs.exists(str(path)) is True
        assert fs.exists(str(tmp_path / "missing.txt")) is False

    def test_is_dir(self, tmp_path):
        fs = OsFileSystem()

        assert fs.is_dir(str(tmp_path)) is True
        assert fs.is_dir(str(tmp_path / "missing")) is False

    def test_make_dir(self, tmp_path):
        path = tmp_path / "nested" / "directory"

        fs = OsFileSystem()
        fs.make_dir(str(path))

        assert path.is_dir()

    def test_write_file(self, tmp_path):
        path = tmp_path / "nested" / "file.txt"

        fs = OsFileSystem()
        fs.write_file(str(path), "hello world")

        assert path.read_text(encoding="utf-8") == "hello world"

    def test_read_file(self, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("hello", encoding="utf-8")

        fs = OsFileSystem()

        assert fs.read_file(str(path)) == "hello"

    def test_copy_tree(self, tmp_path):
        source = tmp_path / "source"
        destination = tmp_path / "destination"

        source.mkdir()
        (source / "file.txt").write_text("hello")

        fs = OsFileSystem()
        fs.copy_tree(str(source), destination)

        assert (
            destination / "file.txt"
        ).read_text() == "hello"

    def test_remove_dir(self, tmp_path):
        path = tmp_path / "directory"
        path.mkdir()
        (path / "file.txt").write_text("hello")

        fs = OsFileSystem()
        fs.remove_dir(str(path))

        assert not path.exists()

    def test_default_author(self, monkeypatch):
        monkeypatch.setattr(
            "qyro.adapters.persistence.storage.getpass.getuser",
            lambda: "test-user",
        )

        fs = OsFileSystem()

        assert fs.default_author() == "test-user"

    def test_default_author_fallback(self, monkeypatch):
        def raise_error():
            raise RuntimeError("failure")

        monkeypatch.setattr(
            "qyro.adapters.persistence.storage.getpass.getuser",
            raise_error,
        )

        fs = OsFileSystem()

        assert fs.default_author() == "Unknown"


class TestSettingsRepository:
    def test_get(self, monkeypatch):
        import qyro

        monkeypatch.setattr(
            qyro,
            "SETTINGS",
            {"project_name": "MyApp"},
            raising=False,
        )

        repository = SettingsRepository()

        assert repository.get("project_name") == "MyApp"

    def test_get_missing_setting(self, monkeypatch):
        import qyro

        monkeypatch.setattr(
            qyro,
            "SETTINGS",
            {},
            raising=False,
        )

        repository = SettingsRepository()

        with pytest.raises(MissingSettingError):
            repository.get("missing")

    def test_get_optional(self, monkeypatch):
        import qyro

        monkeypatch.setattr(
            qyro,
            "SETTINGS",
            {},
            raising=False,
        )

        repository = SettingsRepository()

        assert repository.get_optional(
            "missing",
            "default",
        ) == "default"

    def test_get_optional_existing_value(self, monkeypatch):
        import qyro

        monkeypatch.setattr(
            qyro,
            "SETTINGS",
            {"name": "MyApp"},
            raising=False,
        )

        repository = SettingsRepository()

        assert repository.get_optional(
            "name",
            "default",
        ) == "MyApp"

    def test_set(self, monkeypatch):
        import qyro

        settings = {}

        monkeypatch.setattr(
            qyro,
            "SETTINGS",
            settings,
            raising=False,
        )

        repository = SettingsRepository()
        repository.set("name", "MyApp")

        assert settings == {"name": "MyApp"}

    def test_base_settings_path(self):
        repository = SettingsRepository()

        assert (
            repository.base_settings_path
            == "src/build/settings/base.json"
        )

    def test_activate_profile(self, monkeypatch):
        import qyro

        activate_profile = MagicMock()

        monkeypatch.setattr(
            qyro,
            "activate_profile",
            activate_profile,
            raising=False,
        )

        repository = SettingsRepository()
        repository.activate_profile("development")

        activate_profile.assert_called_once_with(
            "development"
        )

    def test_persist_base(self, monkeypatch):
        import qyro

        update_json = MagicMock()
        path = MagicMock(return_value="/project/base.json")

        qyro_module = sys.modules["qyro"]

        builtin_commands = types.ModuleType(
            "qyro.builtin_commands"
        )
        util = types.ModuleType(
            "qyro.builtin_commands._util"
        )
        util.update_json = update_json

        monkeypatch.setattr(
            qyro_module,
            "path",
            path,
            raising=False,
        )

        monkeypatch.setitem(
            sys.modules,
            "qyro.builtin_commands",
            builtin_commands,
        )
        monkeypatch.setitem(
            sys.modules,
            "qyro.builtin_commands._util",
            util,
        )

        repository = SettingsRepository()

        values = {
            "name": "MyApp",
            "version": "1.0.0",
        }

        repository.persist_base(values)

        path.assert_called_once_with(
            "src/build/settings/base.json"
        )
        update_json.assert_called_once_with(
            "/project/base.json",
            values,
        )


class TestComponentFileWriter:
    def test_target_path(self, tmp_path):
        spec = MagicMock()
        spec.type.directory_name = "views"
        spec.file_name = "main.py"

        writer = ComponentFileWriter(tmp_path)

        result = writer.target_path(spec)

        assert result == str(
            tmp_path
            / "src"
            / "main"
            / "python"
            / "views"
            / "main.py"
        )

    def test_target_exists(self, tmp_path):
        spec = MagicMock()
        spec.type.directory_name = "views"
        spec.file_name = "main.py"

        target = (
            tmp_path
            / "src"
            / "main"
            / "python"
            / "views"
            / "main.py"
        )

        target.parent.mkdir(parents=True)
        target.write_text("print('hello')")

        writer = ComponentFileWriter(tmp_path)

        assert writer.target_exists(spec) is True

    def test_target_does_not_exist(self, tmp_path):
        spec = MagicMock()
        spec.type.directory_name = "views"
        spec.file_name = "main.py"

        writer = ComponentFileWriter(tmp_path)

        assert writer.target_exists(spec) is False

    def test_render(self, monkeypatch, tmp_path):
        component_template = (
            "class $name:\n"
            "    pass\n"
        )

        components = types.ModuleType(
            "qyro.builtin_commands.components"
        )
        components.component_template = component_template

        monkeypatch.setitem(
            sys.modules,
            "qyro.builtin_commands.components",
            components,
        )

        spec = MagicMock()
        spec.template_variables.return_value = {
            "name": "MainView",
        }

        writer = ComponentFileWriter(tmp_path)

        result = writer.render(spec)

        assert result == (
            "class MainView:\n"
            "    pass\n"
        )

    def test_write(self, tmp_path):
        spec = MagicMock()
        spec.type.directory_name = "views"
        spec.file_name = "main.py"

        writer = ComponentFileWriter(tmp_path)

        result = writer.write(
            spec,
            "print('hello')",
        )

        target_dir = (
            tmp_path
            / "src"
            / "main"
            / "python"
            / "views"
        )

        assert result == str(target_dir)
        assert (
            target_dir / "main.py"
        ).read_text(encoding="utf-8") == "print('hello')"
