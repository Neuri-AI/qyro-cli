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
    InvalidBindingError,
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

        raw_binding = self.settings.get("binding")
        try:
            binding = Binding.parse(raw_binding)
        except InvalidBindingError:
            raise MissingBindingError(Binding.values())

        if not self.modules.is_installed(binding.import_name):
            raise MissingBindingError((binding.value))

        current_dir = self.fs.resolve(".")

        entry_point = self.settings.get("entry_point")
        entry_point_path = Path(current_dir) / str(entry_point)

        if not self.fs.exists(str(entry_point_path)):
            raise EntryPointNotFoundError(str(entry_point_path))

        exit_code = self.app_runner.run_from_source(
            main_module_path=str(entry_point_path),
            source_root=current_dir,
        )

        if exit_code != 0:
            raise ApplicationExecutionError(exit_code)