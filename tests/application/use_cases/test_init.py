
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from qyro.application.use_cases.init import InitProjectUseCase
from qyro.domain.errors import ProjectAlreadyExistsError
from qyro.domain.project import (
    AddonModule,
    Binding,
    TargetPlatform,
)
from qyro.domain.version import Version


def make_use_case():
    ui = Mock()
    fs = Mock()
    modules = Mock()
    installer = Mock()
    templates = Mock()
    settings = Mock()

    use_case = InitProjectUseCase(
        ui=ui,
        fs=fs,
        modules=modules,
        installer=installer,
        templates=templates,
        settings_repo=settings,
    )

    return use_case, ui, fs, modules, installer, templates, settings


class TestInitProjectUseCase:
    def test_execute_raises_when_project_already_exists(self, tmp_path):
        use_case, ui, fs, modules, installer, templates, settings = (
            make_use_case()
        )

        fs.exists.return_value = True

        with pytest.raises(ProjectAlreadyExistsError) as exc_info:
            use_case.execute(str(tmp_path))

        assert exc_info.value.path == str(tmp_path.resolve())

        ui.info.assert_not_called()
        templates.resolve_template.assert_not_called()
        fs.copy_tree.assert_not_called()

    def test_execute_uses_preselected_binding(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"
        modules.is_installed.return_value = True
        ui.ask_choice.return_value = "Desktop (x86)"
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = []
        ui.confirm.return_value = False

        use_case.execute(
            target_dir=str(tmp_path),
            preselected_binding="PySide6",
        )

        choices = [call.args[0] for call in ui.ask_choice.call_args_list]

        assert choices == ["Select target platform"]

    def test_execute_rejects_binding_not_supported_by_platform(
        self,
        tmp_path,
    ):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        fs.exists.return_value = False
        ui.ask_choice.return_value = "iPhone"

        with pytest.raises(ValueError, match="not available"):
            use_case.execute(
                target_dir=str(tmp_path),
                preselected_binding="PyQt6",
            )

    def test_execute_installs_missing_binding(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = []
        ui.confirm.return_value = True

        modules.is_installed.return_value = False

        use_case.execute(target_dir=str(tmp_path))

        installer.install.assert_called_once_with("PySide6")

    def test_execute_installs_missing_addons(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = [
            "Pydux (Redux-style State Management)",
            "Sentry (Crash Reporting Integration)",
        ]
        ui.confirm.return_value = True

        modules.is_installed.side_effect = [
            True,
            False,
            False,
        ]

        use_case.execute(target_dir=str(tmp_path))

        assert installer.install.call_args_list == [
            ((AddonModule.PYDUX.value,), {}),
            ((AddonModule.SENTRY.value,), {}),
        ]

    def test_execute_does_not_install_already_installed_dependencies(
        self,
        tmp_path,
    ):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = [
            "Pydux (Redux-style State Management)",
        ]
        ui.confirm.return_value = False

        modules.is_installed.return_value = True

        use_case.execute(target_dir=str(tmp_path))

        installer.install.assert_not_called()

    def test_execute_aborts_before_installing_or_resolving_template(
        self,
        tmp_path,
    ):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = []
        ui.confirm.return_value = False

        use_case.execute(target_dir=str(tmp_path))

        installer.install.assert_not_called()
        templates.resolve_template.assert_not_called()
        fs.copy_tree.assert_not_called()
        fs.write_file.assert_not_called()

        ui.info.assert_any_call("Operation aborted by user.")

    def test_execute_resolves_template_without_explicit_version(
        self,
        tmp_path,
    ):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        template_dir = Path("/templates/pyside6")
        templates.resolve_template.return_value = template_dir

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"
        modules.is_installed.return_value = True

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = []
        ui.confirm.return_value = True

        use_case.execute(target_dir=str(tmp_path))

        templates.resolve_template.assert_called_once_with(
            binding=Binding.PYSIDE6,
            target_platform=TargetPlatform.X86,
            version=None,
        )

    def test_execute_resolves_requested_template_version(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        template_dir = Path("/templates/pyside6")
        templates.resolve_template.return_value = template_dir

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"
        modules.is_installed.return_value = True

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = []
        ui.confirm.return_value = True

        use_case.execute(
            target_dir=str(tmp_path),
            template_version="1.1.0",
        )

        templates.resolve_template.assert_called_once_with(
            binding=Binding.PYSIDE6,
            target_platform=TargetPlatform.X86,
            version=Version.parse("1.1.0"),
        )

    def test_execute_copies_template_to_destination(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        template_dir = Path("/templates/pyside6")
        templates.resolve_template.return_value = template_dir

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"
        modules.is_installed.return_value = True

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = []
        ui.confirm.return_value = True

        use_case.execute(target_dir=str(tmp_path))

        fs.copy_tree.assert_called_once_with(
            template_dir,
            tmp_path.resolve(),
        )

    def test_execute_writes_base_settings(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        template_dir = Path("/templates/pyside6")
        templates.resolve_template.return_value = template_dir

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"
        modules.is_installed.return_value = True

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.2.3",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = []
        ui.confirm.return_value = True

        use_case.execute(target_dir=str(tmp_path))

        expected_settings = {
            "binding": "PySide6",
            "version": "1.2.3",
            "hidden_imports": ["__future__"],
        }

        fs.write_file.assert_called_once_with(
            str(tmp_path.resolve() / "src" / "build" / "base.json"),
            json.dumps(expected_settings, indent=2),
        )

    def test_execute_configures_ios_bundle_identifier(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        template_dir = Path("/templates/pyside6")
        templates.resolve_template.return_value = template_dir

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"
        modules.is_installed.return_value = True

        ui.ask_choice.side_effect = [
            "iPhone",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
            "com.john.myapp",
        ]
        ui.ask_multi_choice.return_value = []
        ui.confirm.return_value = True

        use_case.execute(target_dir=str(tmp_path))

        summary = ui.show_summary.call_args.args[1]

        assert summary["Mac bundle identifier"] == "com.john.myapp"

    def test_execute_limits_mobile_addons_to_pydux(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        template_dir = Path("/templates/pyside6")
        templates.resolve_template.return_value = template_dir

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"
        modules.is_installed.return_value = True

        ui.ask_choice.side_effect = [
            "Android",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "1.0.0",
            "John Doe",
        ]
        ui.ask_multi_choice.return_value = [
            "Pydux (Redux-style State Management)",
        ]
        ui.confirm.return_value = True

        use_case.execute(target_dir=str(tmp_path))

        selected_options = ui.ask_multi_choice.call_args.args[1]

        assert selected_options == [
            "Pydux (Redux-style State Management)"
        ]

        templates.resolve_template.assert_called_once_with(
            binding=Binding.PYSIDE6,
            target_platform=TargetPlatform.ANDROID,
            version=None,
        )

    def test_execute_parses_version_before_confirmation(self, tmp_path):
        (
            use_case,
            ui,
            fs,
            modules,
            installer,
            templates,
            settings,
        ) = make_use_case()

        fs.exists.return_value = False
        fs.default_author.return_value = "John Doe"

        ui.ask_choice.side_effect = [
            "Desktop (x86)",
            "PySide6",
        ]
        ui.ask_text.side_effect = [
            "MyApp",
            "not-a-version",
            "John Doe",
        ]

        with pytest.raises(Exception):
            use_case.execute(target_dir=str(tmp_path))

        ui.confirm.assert_not_called()
        templates.resolve_template.assert_not_called()
