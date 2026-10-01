"""
Module entry point.

Allows invoking the CLI directly via:

    python -m qyro <command> [options]
"""

import sys

from qyro_cli.cmdline import main


if __name__ == "__main__":
    sys.exit(main())