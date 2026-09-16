
import argparse

from qyro.cmdline.commands.create import CreateCommand


def test_configure_defines_create_arguments():
    parser = argparse.ArgumentParser()

    CreateCommand.configure(parser)

    args = parser.parse_args(
        ["component", "LoginForm"],
    )

    assert args.type == "component"
    assert args.name == "LoginForm"
    assert args.inherit == "QWidget"


def test_configure_accepts_custom_inheritance():
    parser = argparse.ArgumentParser()

    CreateCommand.configure(parser)

    args = parser.parse_args(
        ["view", "MainWindow", "--inherit", "QMainWindow"],
    )

    assert args.type == "view"
    assert args.name == "MainWindow"
    assert args.inherit == "QMainWindow"


def test_configure_rejects_invalid_type():
    parser = argparse.ArgumentParser()

    CreateCommand.configure(parser)

    try:
        parser.parse_args(["service", "UserService"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected invalid type to be rejected")


def test_execute_prints_selected_values(capsys):
    args = argparse.Namespace(
        type="component",
        name="LoginForm",
        inherit="QWidget",
    )

    result = CreateCommand.execute(args)

    captured = capsys.readouterr()

    assert result == 0
    assert (
        captured.out
        == "Create command selected: "
        "type='component', "
        "name='LoginForm', "
        "inherit='QWidget'\n"
    )
