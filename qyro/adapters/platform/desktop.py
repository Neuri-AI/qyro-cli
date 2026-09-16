"""Windows and macOS platform adapters."""

from os.path import exists, join, relpath
from typing import Optional

from qyro.adapters.platform.base import BasePlatform
from qyro.domain.instructions import FreezeResult, InstallerResult


class WindowsPlatform(BasePlatform):
    name = "Windows"

    def freeze(self, app_name: str, debug: bool) -> FreezeResult:
        from qyro.freeze.windows import freeze_windows
        freeze_windows(debug=debug)
        return FreezeResult(join("target", app_name, app_name + ".exe"))

    def supports_signing(self) -> bool:
        return True

    def sign_app(self) -> Optional[str]:
        from qyro import path
        from qyro.sign.windows import sign_windows
        sign_windows()
        return (
            "Signed all binary files in "
            f"{relpath(path('${freeze_dir}'), path('.'))} and its "
            "subdirectories."
        )

    def has_codesigning_certificate(self) -> bool:
        from qyro import path
        from qyro.sign.windows import _CERTIFICATE_PATH
        return exists(path(_CERTIFICATE_PATH))

    def create_installer(
        self, app_name: str, installer_file: str, user_level: bool
    ) -> InstallerResult:
        from qyro.installer.windows import create_installer_windows
        create_installer_windows(user_level=user_level)
        return InstallerResult(output_file=join("target", installer_file))

    def supports_signing_installer(self) -> bool:
        return True

    def sign_installer(self) -> None:
        from qyro.sign_installer.windows import sign_installer_windows
        sign_installer_windows()


class MacPlatform(BasePlatform):
    name = "macOS"

    def freeze(self, app_name: str, debug: bool) -> FreezeResult:
        from qyro.freeze.mac import freeze_mac
        freeze_mac(debug=debug)
        return FreezeResult(
            f"target/{app_name}.app/Contents/MacOS/{app_name}"
        )

    def supports_signing(self) -> bool:
        # PPG does not implement `sign` on macOS yet.
        return False

    def create_installer(
        self, app_name: str, installer_file: str, user_level: bool
    ) -> InstallerResult:
        from qyro.installer.mac import create_installer_mac
        create_installer_mac()
        return InstallerResult(output_file=join("target", installer_file))