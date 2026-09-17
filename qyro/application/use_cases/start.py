from pathlib import Path

from qyro.application.guards import ProjectGuards
from qyro.application.ports import (
    AppRunnerPort,
    FileSystemPort,
    ImportlibModuleRegistry,
    SettingsPort,
    UserInteractionPort,
)
from qyro.domain.errors import (
    ApplicationExecutionError,
    EntryPointNotFoundError,
    MissingBindingError,
)
from qyro.domain.project import Binding


class RunApplicationUseCase:
    def __init__(
        self,
        ui: UserInteractionPort,
        fs: FileSystemPort,
        settings: SettingsPort,
        app_runner: AppRunnerPort,
        modules: ImportlibModuleRegistry,
        guards: ProjectGuards,
    ):
        self.ui = ui
        self.fs = fs
        self.settings = settings
        self.app_runner = app_runner
        self.modules = modules
        self.guards = guards

    def execute(self) -> None:
        self.guards.require_existing_project()

        if not any(
            self.modules.is_installed(binding.value)
            for binding in Binding
        ):
            raise MissingBindingError(
                tuple(binding.value for binding in Binding)
            )

        current_dir = self.fs.resolve(".")

        entry_point = self.settings.get("entry_point")
        entry_point_path = Path(current_dir) / str(entry_point)

        binding = self.settings.get("binding")
        if binding not in (b.value for b in Binding):
            raise MissingBindingError(tuple(binding.value for binding in Binding))

        if not self.fs.exists(str(entry_point_path)):
            raise EntryPointNotFoundError(str(entry_point_path))

        exit_code = self.app_runner.run_from_source(
            main_module_path=str(entry_point_path),
            source_root=current_dir,
        )

        if exit_code != 0:
            raise ApplicationExecutionError(exit_code)
