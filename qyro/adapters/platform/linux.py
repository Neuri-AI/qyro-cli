"""
Linux platform adapters.

Each distribution owns its shell instructions *in one place*. Previously the
same apt/pacman/dnf command strings were written twice — once in `installer()`
and again in `upload()` — and could drift apart. Now `installer`, `repo` and
`upload` all read them from the same adapter.
"""

from os.path import join

from ppg.adapters.platform.base import BasePlatform
from ppg.domain.instructions import (
    FreezeResult, InstallerResult, RepoResult, ShellInstructions, UploadResult,
)


class LinuxPlatform(BasePlatform):
    """Generic Linux: it can freeze, but has no packaging story."""

    name = "Linux"

    def freeze(self, app_name: str, debug: bool) -> FreezeResult:
        from ppg.freeze.linux import freeze_linux
        freeze_linux(debug=debug)
        return FreezeResult(join("target", app_name, app_name))


class UbuntuPlatform(LinuxPlatform):
    name = "Ubuntu"

    def freeze(self, app_name: str, debug: bool) -> FreezeResult:
        from ppg.freeze.ubuntu import freeze_ubuntu
        freeze_ubuntu(debug=debug)
        return FreezeResult(join("target", app_name, app_name))

    def create_installer(
        self, app_name: str, installer_file: str, user_level: bool
    ) -> InstallerResult:
        from ppg.installer.ubuntu import create_installer_ubuntu
        create_installer_ubuntu()
        out_file = join("target", installer_file)
        return InstallerResult(
            output_file=out_file,
            install=ShellInstructions(
                heading="You can for instance install it via the following "
                        "command:",
                commands=[f"sudo dpkg -i {out_file}"],
            ),
            uninstall=ShellInstructions(
                heading="To uninstall it again, you can use:",
                commands=[f"sudo dpkg --purge {app_name}"],
            ),
            install_location=f"/opt/{app_name}",
        )

    def supports_signing_installer(self) -> bool:
        # Ubuntu does not support signing installers.
        return False

    def supports_repo(self) -> bool:
        return True

    def create_repo(self, app_name: str, gpg_key: str) -> RepoResult:
        from ppg import path
        from ppg.repo.ubuntu import create_repo_ubuntu
        create_repo_ubuntu()
        pkg = app_name.lower()
        repo_path = path("target/repo")
        public_key = path("src/sign/linux/public-key.gpg")
        return RepoResult(
            setup=ShellInstructions(commands=[
                f'echo "deb [arch=amd64] file://{repo_path} stable main" '
                f"| sudo tee /etc/apt/sources.list.d/{pkg}.list",
                f"sudo apt-key add {public_key}",
                "sudo apt-get update",
                f"sudo apt-get install {pkg}",
            ]),
            revert=ShellInstructions(commands=[
                f"sudo dpkg --purge {pkg}",
                f"sudo apt-key del {gpg_key}",
                f"sudo rm /etc/apt/sources.list.d/{pkg}.list",
                "sudo apt-get update",
            ]),
        )

    def upload_instructions(
        self, app_name, base_url, installer_url, repo_url, gpg_key
    ) -> UploadResult:
        pkg = app_name.lower()
        return UploadResult(
            installer_url=installer_url,
            install=ShellInstructions(
                heading="Your users can now install your app via the "
                        "following commands:",
                commands=[
                    "sudo apt-get install apt-transport-https",
                    f"wget -qO - {base_url}/public-key.gpg | sudo apt-key add -",
                    f"echo 'deb [arch=amd64] {repo_url} stable main' | "
                    f"sudo tee /etc/apt/sources.list.d/{pkg}.list",
                    "sudo apt-get update",
                    f"sudo apt-get install {pkg}",
                ],
            ),
            force_update=ShellInstructions(commands=[
                "sudo apt-get update "
                f'-o Dir::Etc::sourcelist="/etc/apt/sources.list.d/{pkg}.list" '
                '-o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0"',
                f"sudo apt-get install --only-upgrade {pkg}",
            ]),
            notes=[
                "Finally, your users can also install without automatic "
                f"updates by downloading:\n    {installer_url}"
            ],
        )


class ArchPlatform(LinuxPlatform):
    name = "Arch Linux"

    def freeze(self, app_name: str, debug: bool) -> FreezeResult:
        from ppg.freeze.arch import freeze_arch
        freeze_arch(debug=debug)
        return FreezeResult(join("target", app_name, app_name))

    def create_installer(
        self, app_name: str, installer_file: str, user_level: bool
    ) -> InstallerResult:
        from ppg.installer.arch import create_installer_arch
        create_installer_arch()
        out_file = join("target", installer_file)
        return InstallerResult(
            output_file=out_file,
            install=ShellInstructions(
                heading="You can for instance install it via the following "
                        "command:",
                commands=[f"sudo pacman -U {out_file}"],
            ),
            uninstall=ShellInstructions(
                heading="To uninstall it again, you can use:",
                commands=[f"sudo pacman -R {app_name}"],
            ),
            install_location=f"/opt/{app_name}",
        )

    def supports_signing_installer(self) -> bool:
        return True

    def sign_installer(self) -> None:
        from ppg.sign_installer.arch import sign_installer_arch
        sign_installer_arch()

    def supports_repo(self) -> bool:
        return True

    def create_repo(self, app_name: str, gpg_key: str) -> RepoResult:
        from ppg import path
        from ppg.repo.arch import create_repo_arch
        create_repo_arch()
        pkg = app_name.lower()
        repo_path = path("target/repo")
        public_key = path("src/sign/linux/public-key.gpg")
        return RepoResult(
            setup=ShellInstructions(commands=[
                "sudo cp /etc/pacman.conf /etc/pacman.conf.bu",
                f"echo -e '\\n[{app_name}]\\nServer = file://{repo_path}' "
                "| sudo tee -a /etc/pacman.conf",
                f"sudo pacman-key --add {public_key}",
                f"sudo pacman-key --lsign-key {gpg_key}",
                f"sudo pacman -Syu {pkg}",
            ]),
            revert=ShellInstructions(commands=[
                f"sudo pacman -R {pkg}",
                f"sudo pacman-key --delete {gpg_key}",
                "sudo mv /etc/pacman.conf.bu /etc/pacman.conf",
            ]),
        )

    def upload_instructions(
        self, app_name, base_url, installer_url, repo_url, gpg_key
    ) -> UploadResult:
        pkg = app_name.lower()
        return UploadResult(
            installer_url=installer_url,
            install=ShellInstructions(
                heading="Your users can now install your app via the "
                        "following commands:",
                commands=[
                    f"curl -O {base_url}/public-key.gpg && "
                    "sudo pacman-key --add public-key.gpg && "
                    f"sudo pacman-key --lsign-key {gpg_key} && "
                    "rm public-key.gpg",
                    f"echo -e '\\n[{app_name}]\\nServer = {repo_url}' | "
                    "sudo tee -a /etc/pacman.conf",
                    f"sudo pacman -Syu {pkg}",
                ],
            ),
            force_update=ShellInstructions(
                commands=[f"sudo pacman -Syu --needed {pkg}"]
            ),
            notes=[
                "Finally, your users can also install without automatic "
                f"updates by downloading:\n    {installer_url}"
            ],
        )


class FedoraPlatform(LinuxPlatform):
    name = "Fedora"

    def freeze(self, app_name: str, debug: bool) -> FreezeResult:
        from ppg.freeze.fedora import freeze_fedora
        freeze_fedora(debug=debug)
        return FreezeResult(join("target", app_name, app_name))

    def create_installer(
        self, app_name: str, installer_file: str, user_level: bool
    ) -> InstallerResult:
        from ppg.installer.fedora import create_installer_fedora
        create_installer_fedora()
        out_file = join("target", installer_file)
        return InstallerResult(
            output_file=out_file,
            install=ShellInstructions(
                heading="You can for instance install it via the following "
                        "command:",
                commands=[f"sudo dnf install {out_file}"],
            ),
            uninstall=ShellInstructions(
                heading="To uninstall it again, you can use:",
                commands=[f"sudo dnf remove {app_name}"],
            ),
            install_location=f"/opt/{app_name}",
        )

    def supports_signing_installer(self) -> bool:
        return True

    def sign_installer(self) -> None:
        from ppg.sign_installer.fedora import sign_installer_fedora
        sign_installer_fedora()

    def supports_repo(self) -> bool:
        return True

    def create_repo(self, app_name: str, gpg_key: str) -> RepoResult:
        from ppg import SETTINGS, path
        from ppg.repo.fedora import create_repo_fedora
        create_repo_fedora()
        pkg = app_name.lower()
        public_key = path("src/sign/linux/public-key.gpg")
        project_dir = SETTINGS["project_dir"]
        return RepoResult(
            setup=ShellInstructions(commands=[
                f"sudo rpm -v --import {public_key}",
                "sudo dnf config-manager --add-repo "
                f"file://{project_dir}/target/repo",
                f"sudo dnf install {pkg}",
            ]),
            revert=ShellInstructions(commands=[
                f"sudo dnf remove {pkg}",
                f"sudo rm /etc/yum.repos.d/*{app_name}*.repo",
                f"sudo rpm --erase gpg-pubkey-{gpg_key[-8:].lower()}",
            ]),
        )

    def upload_instructions(
        self, app_name, base_url, installer_url, repo_url, gpg_key
    ) -> UploadResult:
        pkg = app_name.lower()
        return UploadResult(
            installer_url=installer_url,
            install=ShellInstructions(
                heading="Your users can now install your app via the "
                        "following commands:",
                commands=[
                    f"sudo rpm -v --import {base_url}/public-key.gpg",
                    "sudo dnf config-manager --add-repo "
                    f"{repo_url}/{app_name}.repo",
                    f"sudo dnf install {pkg}",
                ],
                footer="(On CentOS, replace 'dnf' by 'yum' and "
                       "'dnf config-manager' by 'yum-config-manager'.)",
            ),
            force_update=ShellInstructions(
                commands=[f"sudo dnf upgrade {pkg} --refresh"],
                footer="This is for Fedora. For CentOS, use:\n"
                       f"    sudo yum clean all && sudo yum upgrade {pkg}",
            ),
            notes=[
                "Finally, your users can also install without automatic "
                f"updates by downloading:\n    {installer_url}"
            ],
        )