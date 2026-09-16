"""
Concrete presentation adapter implementing UserInteractionPort
using Rich and Questionary.
"""

from typing import Sequence

import questionary
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table


QUESTIONARY_STYLE = Style([
    ("qmark", "fg:#ff00ff bold"),
    ("question", "fg:#00ffff bold"),
    ("answer", "fg:#00ffff bold"),
    ("pointer", "fg:#ffff00 bold"),
    ("highlighted", "fg:#2fe784 bold"),
    ("selected", "fg:#2fe784 bold"),
])


class RichConsoleUI:
    def __init__(self, console: Console | None = None):
        self._console = console or Console()

    def ask_text(
        self,
        prompt: str,
        default: str = "",
        show_default: bool = True,
    ) -> str:
        return Prompt.ask(
            f"[bold]{prompt}[/bold]",
            default=default,
            show_default=show_default,
        )

    def ask_choice(
        self,
        prompt: str,
        choices: Sequence[str],
        default: str = "",
    ) -> str:
        options = list(choices)

        if not options:
            return default

        answer = questionary.select(
            f"{prompt} [{'/'.join(options)}] ({default}):",
            choices=options,
            default=default or options[0],
            style=QUESTIONARY_STYLE,
        ).ask()

        if answer is None:
            raise KeyboardInterrupt

        return answer

    def ask_multi_choice(
        self,
        prompt: str,
        choices: Sequence[str],
    ) -> list[str]:
        answer = questionary.checkbox(
            prompt,
            choices=[
                questionary.Choice(
                    choice,
                    value=choice,
                    checked=False,
                )
                for choice in choices
            ],
            style=QUESTIONARY_STYLE,
        ).ask()

        if answer is None:
            raise KeyboardInterrupt

        return answer

    def confirm(
        self,
        prompt: str,
        default: bool = True,
    ) -> bool:
        return Confirm.ask(
            f"[bold yellow]{prompt}[/bold yellow]",
            default=default,
        )

    def show_summary(
        self,
        title: str,
        fields: dict[str, str],
    ) -> None:
        table = Table(
            title="Project Configuration",
            show_header=False,
            box=None,
        )

        for label, value in fields.items():
            table.add_row(
                f"{label}:",
                f"[cyan]{value}[/cyan]",
            )

        self._console.print(
            Panel(
                table,
                title=f"[bold]{title}[/bold]",
                border_style="blue",
            )
        )

    def info(self, message: str) -> None:
        self._console.print(message)

    def success(self, message: str) -> None:
        self._console.print(
            f"\n🎉 [bold green]{message}[/bold green]"
        )

    def warning(self, message: str) -> None:
        self._console.print(
            f"[yellow]{message}[/yellow]"
        )

    def progress(self, message: str) -> None:
        self._console.print(
            f"⏳ {message}"
        )

    def error(self, message: str) -> None:
        self._console.print(
            f"\n💔 [bold red]Error:[/bold red] {message}"
        )
