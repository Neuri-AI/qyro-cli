"""
Implementation of the `qyro init` command.
"""

import argparse

from qyro.cmdline.registry import command
from qyro.container import get_container


@command(
    "init",
    help="Initialize a new Qyro project.",
)
class InitCommand:
    """Initialize a new Qyro project."""

    @staticmethod
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-n",
            "--name",
            nargs="?",
            default=".",
            help=(
                "Project directory name. "
                "Defaults to the current directory."
            ),
        )

        parser.add_argument(
            "-b",
            "--binding",
            choices=[
                "PySide6",
                "PyQt6",
                "PyQt5",
                "PySide2",
                "Kivy",
                "Tkinter",
            ],
            help="Pre-select the UI binding.",
        )

        parser.add_argument(
            "--template-version",
            help="Use a specific template version.",
        )

    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        get_container().init_project_use_case.execute(
            target_dir=args.name,
            preselected_binding=args.binding,
            template_version=args.template_version,
        )

        return 0
