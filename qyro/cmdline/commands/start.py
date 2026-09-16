# qyro/cmdline/commands/start.py
"""
Implementation of the `qyro start` command.
"""

import argparse

from qyro.cmdline.registry import command


@command(
    "start",
    help="Start the application in development mode.",
)
class StartCommand:
    """Start the application in development mode."""

    @staticmethod
    def configure(parser: argparse.ArgumentParser) -> None:
        pass

    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        """
        Execute the start command.

        Application-layer integration will be connected here once
        the corresponding use case is available.
        """

        print("Start command selected.")

        return 0