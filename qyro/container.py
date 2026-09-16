"""
qyro.container
Composition Root implementing Inversion of Control (IoC).
All dependencies between Use Cases, Ports, and Adapters are instantiated here.
"""

from pathlib import Path

from qyro.adapters.cli.console_ui import RichConsoleUI
from qyro.adapters.package.metadata import PackageMetadata
from qyro.adapters.persistence.storage import (
    OsFileSystem,
    SettingsRepository,
)
from qyro.adapters.process.runners import (
    ImportlibModuleRegistry,
    SubprocessAppRunner,
    SubprocessRunner,
)
from qyro.adapters.process.dependencies import DependencyInstaller
from qyro.adapters.templates.bundled import BundledTemplateProvider
from qyro.adapters.templates.fallback import FallbackTemplateProvider
from qyro.adapters.templates.github_cached import (
    GitHubCachedTemplateProvider,
)
from qyro.application.use_cases.init import InitProjectUseCase
from qyro.application.use_cases.version import ShowVersionUseCase
from qyro.adapters.cli.progress import RichProgress


# BUILDERS
# from qyro.adapters.platform.factory import PlatformStrategyFactory
# from qyro.adapters.mobile.pyside_deploy import PySideMobileDeployer
# from qyro.application.use_cases.build import BuildDesktopUseCase
# from qyro.application.use_cases.mobile_build import MobileBuildUseCase


TEMPLATE_ORGANIZATION = "Neuri-AI"
TEMPLATE_CACHE_DIR = Path.home() / ".qyro" / "templates"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


class Container:
    """Dependency Injection Container."""

    def __init__(self):
        self.ui = RichConsoleUI()
        self.fs = OsFileSystem()
        self.settings = SettingsRepository()
        self.app_runner = SubprocessAppRunner()
        self.subprocess_runner = SubprocessRunner()
        dependency_installer = DependencyInstaller(
            runner=self.subprocess_runner,
        )
        self.modules = ImportlibModuleRegistry()
        self.metadata = PackageMetadata()
        self.progress = RichProgress()

        github_provider = GitHubCachedTemplateProvider(
            organization=TEMPLATE_ORGANIZATION,
            cache_dir=TEMPLATE_CACHE_DIR,
            supported_range="^1.0.0",
            progress=self.progress,
        )

        bundled_provider = BundledTemplateProvider(
            templates_dir=TEMPLATE_DIR,
        )

        self.template_provider = FallbackTemplateProvider(
            primary=github_provider,
            fallback=bundled_provider,
        )

        self.init_project_use_case = InitProjectUseCase(
            ui=self.ui,
            fs=self.fs,
            dependencies=dependency_installer,
            templates=self.template_provider,
            settings_repo=self.settings,
        )

        self.show_version_use_case = ShowVersionUseCase(
            ui=self.ui,
            metadata=self.metadata,
        )


_container: Container | None = None


def get_container() -> Container:
    global _container

    if _container is None:
        _container = Container()

    return _container


def set_container(container: Container) -> None:
    """Replace the container, primarily for tests."""
    global _container
    _container = container
