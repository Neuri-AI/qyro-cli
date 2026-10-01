"""
Concrete adapter for retrieving Qyro package metadata.
"""

from importlib.metadata import version


class PackageMetadata:
    def qyro_version(self) -> str:
        return version("qyro")