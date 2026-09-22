# qyro/cmdline/commands/clean.py
"""
Implementation of the `qyro clean` command.
"""

import argparse
from qyro.cmdline.registry import command


@command(
    "clean",
    help="Remove target build outputs and log files.",
)
class CleanCommand:
    """Clean generated project artifacts."""

    @staticmethod
    def configure(parser: argparse.ArgumentParser) -> None:
        pass

    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        """
        Execute the clean command.

        Application-layer integration will be connected here once
        the corresponding use case is available.
        """

        print("Clean command selected.")

        return 0