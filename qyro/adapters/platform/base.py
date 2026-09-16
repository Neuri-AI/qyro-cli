"""
Base class for platform adapters.

Sensible "not supported" defaults live here, so each concrete platform only
overrides what it actually does. A new distribution is one small subclass.
"""

from typing import Optional

from qyro.domain.instructions import (
    FreezeResult, InstallerResult, RepoResult, ShellInstructions, UploadResult,
)


class BasePlatform:
    name = "this platform"

    # -- freeze --------------------------------------------------------------

    def freeze(self, app_name: str, debug: bool) -> FreezeResult:
        raise NotImplementedError

    # -- sign ----------------------------------------------------------------

    def supports_signing(self) -> bool:
        return False

    def sign_app(self) -> Optional[str]:
        return None

    def has_codesigning_certificate(self) -> bool:
        return False

    # -- installer -----------------------------------------------------------

    def create_installer(
        self, app_name: str, installer_file: str, user_level: bool
    ) -> InstallerResult:
        raise NotImplementedError

    def supports_signing_installer(self) -> bool:
        return False

    def sign_installer(self) -> None:
        raise NotImplementedError

    # -- repo ----------------------------------------------------------------

    def supports_repo(self) -> bool:
        return False

    def create_repo(self, app_name: str, gpg_key: str) -> RepoResult:
        raise NotImplementedError

    # -- upload --------------------------------------------------------------

    def upload_instructions(
        self, app_name: str, base_url: str, installer_url: str,
        repo_url: str, gpg_key: str,
    ) -> UploadResult:
        """Default: nothing distro-specific, users just download the file."""
        return UploadResult(
            installer_url=installer_url,
            install=ShellInstructions(),
            force_update=ShellInstructions(),
        )