# qyro/cmdline/commands/create.py
"""
Implementation of the `qyro create` command.
"""

import argparse

from qyro.cmdline.registry import command


@command(
    "create",
    help="Scaffold a component or view.",
)
class CreateCommand:
    """Create a Qyro component or view."""

    @staticmethod
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "type",
            choices=[
                "component",
                "view",
            ],
            help="Item type to generate.",
        )

        parser.add_argument(
            "name",
            help="Name of the component or view.",
        )

        parser.add_argument(
            "--inherit",
            default="QWidget",
            help="Base widget to inherit from.",
        )

    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        """
        Execute the create command.

        Application-layer integration will be connected here once
        the corresponding use case is available.
        """

        print(
            "Create command selected:"
            f" type={args.type!r},"
            f" name={args.name!r},"
            f" inherit={args.inherit!r}"
        )

        return 0