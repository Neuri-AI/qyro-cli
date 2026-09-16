"""
Implementation of the `qyro version` command.
"""

import argparse

from qyro.cmdline.registry import command
from qyro.container import get_container


@command(
    "version",
    help="Show the current Qyro engine version.",
)
class VersionCommand:
    """Display the current Qyro version."""

    @staticmethod
    def configure(parser: argparse.ArgumentParser) -> None:
        pass

    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        get_container().show_version_use_case.execute()
        return 0