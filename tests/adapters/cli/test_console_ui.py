
from unittest.mock import MagicMock, patch
import pytest
from rich.console import Console

from qyro.adapters.cli.console_ui import RichConsoleUI


@pytest.fixture
def console():
    return MagicMock(spec=Console)


@pytest.fixture
def ui(console):
    return RichConsoleUI(console=console)


@patch("qyro.adapters.cli.console_ui.Prompt.ask")
def test_ask_text(mock_ask, ui):
    mock_ask.return_value = "MyApp"

    result = ui.ask_text("Application name")

    assert result == "MyApp"
    mock_ask.assert_called_once_with(
        "[bold]Application name[/bold]",
        default="",
    )


@patch("qyro.adapters.cli.console_ui.Prompt.ask")
def test_ask_text_with_default(mock_ask, ui):
    mock_ask.return_value = "MyApp"

    result = ui.ask_text(
        "Application name",
        default="DefaultApp",
    )

    assert result == "MyApp"
    mock_ask.assert_called_once_with(
        "[bold]Application name[/bold]",
        default="DefaultApp",
    )


def test_ask_choice_without_choices(ui):
    result = ui.ask_choice(
        "Binding",
        [],
        default="PySide6",
    )

    assert result == "PySide6"


@patch("qyro.adapters.cli.console_ui.questionary.select")
def test_ask_choice(mock_select, ui):
    mock_select.return_value.ask.return_value = "PySide6"

    result = ui.ask_choice(
        "Binding",
        ["PySide6", "PyQt6"],
    )

    assert result == "PySide6"

    mock_select.assert_called_once_with(
        "Binding [PySide6/PyQt6] ():",
        choices=["PySide6", "PyQt6"],
        default="PySide6",
        style=ui.__class__.__module__ and mock_select.call_args.kwargs["style"],
    )


@patch("qyro.adapters.cli.console_ui.questionary.select")
def test_ask_choice_returns_default_when_cancelled(
    mock_select,
    ui,
):
    mock_select.return_value.ask.return_value = None

    result = ui.ask_choice(
        "Binding",
        ["PySide6", "PyQt6"],
        default="PyQt6",
    )

    assert result == "PyQt6"


@patch("qyro.adapters.cli.console_ui.questionary.checkbox")
def test_ask_multi_choice(mock_checkbox, ui):
    mock_checkbox.return_value.ask.return_value = [
        "Sentry",
        "Pydux",
    ]

    result = ui.ask_multi_choice(
        "Add-ons",
        ["Hot Reloading", "Pydux", "Sentry"],
    )

    assert result == ["Sentry", "Pydux"]

    mock_checkbox.assert_called_once()

    kwargs = mock_checkbox.call_args.kwargs

    assert kwargs["style"] is not None
    assert len(kwargs["choices"]) == 3
    assert all(
        choice.value == choice.title
        for choice in kwargs["choices"]
    )
    assert all(
        choice.checked is False
        for choice in kwargs["choices"]
    )


@patch("qyro.adapters.cli.console_ui.questionary.checkbox")
def test_ask_multi_choice_returns_empty_list_when_cancelled(
    mock_checkbox,
    ui,
):
    mock_checkbox.return_value.ask.return_value = None

    result = ui.ask_multi_choice(
        "Add-ons",
        ["Sentry"],
    )

    assert result == []


@patch("qyro.adapters.cli.console_ui.Confirm.ask")
def test_confirm(mock_confirm, ui):
    mock_confirm.return_value = True

    result = ui.confirm("Continue?")

    assert result is True
    mock_confirm.assert_called_once_with(
        "[bold yellow]Continue?[/bold yellow]",
        default=True,
    )


@patch("qyro.adapters.cli.console_ui.Confirm.ask")
def test_confirm_with_default(mock_confirm, ui):
    mock_confirm.return_value = False

    result = ui.confirm(
        "Continue?",
        default=False,
    )

    assert result is False
    mock_confirm.assert_called_once_with(
        "[bold yellow]Continue?[/bold yellow]",
        default=False,
    )


def test_show_summary(ui, console):
    ui.show_summary(
        "Project",
        {
            "Name": "MyApp",
            "Binding": "PySide6",
        },
    )

    console.print.assert_called_once()

    panel = console.print.call_args.args[0]

    assert panel.title == "[bold]Project[/bold]"
    assert panel.border_style == "blue"
    assert panel.renderable.title == "Project Configuration"


@pytest.mark.parametrize(
    ("method", "message", "expected"),
    [
        ("info", "hello", "hello"),
        (
            "success",
            "done",
            "\n🎉 [bold green]done[/bold green]",
        ),
        (
            "warning",
            "warning",
            "[yellow]warning[/yellow]",
        ),
        (
            "progress",
            "working",
            "⏳ working",
        ),
        (
            "error",
            "failed",
            "\n💔 [bold red]Error:[/bold red] failed",
        ),
    ],
)
def test_console_messages(
    ui,
    console,
    method,
    message,
    expected,
):
    getattr(ui, method)(message)

    console.print.assert_called_once_with(expected)
