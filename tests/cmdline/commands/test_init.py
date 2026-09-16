
import argparse
from unittest.mock import Mock

from qyro.cmdline.commands.init import InitCommand


def test_configure_defines_init_arguments():
    parser = argparse.ArgumentParser()

    InitCommand.configure(parser)

    args = parser.parse_args([])

    assert args.name == "."
    assert args.binding is None
    assert args.template_version is None


def test_configure_accepts_all_arguments():
    parser = argparse.ArgumentParser()

    InitCommand.configure(parser)

    args = parser.parse_args(
        [
            "--name",
            "MyApp",
            "--binding",
            "PySide6",
            "--template-version",
            "1.2.3",
        ],
    )

    assert args.name == "MyApp"
    assert args.binding == "PySide6"
    assert args.template_version == "1.2.3"


def test_execute_delegates_to_init_use_case(monkeypatch):
    use_case = Mock()
    container = Mock()
    container.init_project_use_case = use_case

    monkeypatch.setattr(
        "qyro.cmdline.commands.init.get_container",
        lambda: container,
    )

    args = argparse.Namespace(
        name="MyApp",
        binding="PySide6",
        template_version="1.2.3",
    )

    result = InitCommand.execute(args)

    assert result == 0

    use_case.execute.assert_called_once_with(
        target_dir="MyApp",
        preselected_binding="PySide6",
        template_version="1.2.3",
    )


def test_execute_passes_none_for_optional_arguments(monkeypatch):
    use_case = Mock()
    container = Mock()
    container.init_project_use_case = use_case

    monkeypatch.setattr(
        "qyro.cmdline.commands.init.get_container",
        lambda: container,
    )

    args = argparse.Namespace(
        name=".",
        binding=None,
        template_version=None,
    )

    result = InitCommand.execute(args)

    assert result == 0

    use_case.execute.assert_called_once_with(
        target_dir=".",
        preselected_binding=None,
        template_version=None,
    )

