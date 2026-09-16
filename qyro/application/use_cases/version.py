"""
qyro.application.use_cases.version
Use case for displaying the installed Qyro version.
"""

from qyro.application.ports import (
    PackageMetadataPort,
    UserInteractionPort,
)


class ShowVersionUseCase:
    def __init__(
        self,
        ui: UserInteractionPort,
        metadata: PackageMetadataPort,
    ):
        self.ui = ui
        self.metadata = metadata

    def execute(self) -> None:
        version = self.metadata.qyro_version()
        self.ui.info(f"Qyro v{version}")