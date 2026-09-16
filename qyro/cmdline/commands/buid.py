"""
Implementation of the `qyro build` command.
"""

import argparse

from qyro.container import Container
from qyro.domain.mobile import MobileTarget

from qyro.cmdline.registry import command


@command(
    "build",
    help="Build and bundle the application.",
    aliases=("freeze",),
)
class BuildCommand:
    """Build the Qyro application."""

    @staticmethod
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--target",
            choices=[
                "desktop",
                "android",
                "ios",
            ],
            default="desktop",
            help="Build target platform.",
        )

        parser.add_argument(
            "--profile",
            choices=[
                "debug",
                "release",
                "prod",
            ],
            default="release",
            help="Build profile.",
        )

        parser.add_argument(
            "--bundle",
            action="store_true",
            help="Package into a single standalone bundle.",
        )

        parser.add_argument(
            "--init-spec",
            action="store_true",
            help="Generate the mobile specification file.",
        )

    @staticmethod
    def execute(
        args: argparse.Namespace,
        container: Container,
    ) -> int:

        if args.target in ("android", "ios"):
            target = (
                MobileTarget.ANDROID
                if args.target == "android"
                else MobileTarget.IOS
            )

            container.mobile_build_use_case.execute(
                target=target,
                init_only=args.init_spec,
                debug=args.profile == "debug",
            )

            return 0

        container.build_desktop_use_case.execute(
            profile=args.profile,
            bundle=args.bundle,
        )

        return 0