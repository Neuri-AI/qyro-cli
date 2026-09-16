"""
The one and only place in the codebase that asks "which OS are we on?".

Everything downstream receives a PlatformPort and doesn't care.
"""

from qyro.adapters.platform.base import BasePlatform
from qyro.adapters.platform.desktop import MacPlatform, WindowsPlatform
from qyro.adapters.platform.linux import (
    ArchPlatform, FedoraPlatform, LinuxPlatform, UbuntuPlatform,
)
from ppg.domain.errors import UnsupportedOSError


def detect_platform() -> BasePlatform:
    from ppg_runtime.platform import (
        is_arch_linux, is_fedora, is_linux, is_mac, is_ubuntu, is_windows,
    )

    if is_windows():
        return WindowsPlatform()
    if is_mac():
        return MacPlatform()
    if is_linux():
        if is_ubuntu():
            return UbuntuPlatform()
        if is_arch_linux():
            return ArchPlatform()
        if is_fedora():
            return FedoraPlatform()
        return LinuxPlatform()
    raise UnsupportedOSError()