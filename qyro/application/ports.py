"""
qyro.application.ports
Application-layer interfaces for peripheral adapters.

These Protocols define what the application layer needs from the outside
world. Implementations belong to infrastructure/presentation adapters.

No concrete infrastructure dependencies are allowed here.
"""

from pathlib import Path
from typing import Any, Optional, Protocol, Sequence
from qyro.domain.version import Version

from qyro.domain.instructions import (
    FreezeResult,
    InstallerResult,
    RepoResult,
    UploadResult,
)
from qyro.domain.mobile import MobileTarget
from qyro.domain.project import (
    Binding,
    ComponentSpec,
    ProjectConfig,
    TargetPlatform,
)


# --- Presentation -----------------------------------------------------------


class UserInteractionPort(Protocol):
    """Everything application use cases need from a human."""

    def welcome(self) -> None: ...

    def ask_text(
        self,
        prompt: str,
        default: str = "",
        show_default: bool = True,
    ) -> str: ...

    def ask_choice(
        self,
        prompt: str,
        choices: Sequence[str],
        default: str = "",
    ) -> str: ...

    def ask_multi_choice(
        self,
        prompt: str,
        choices: Sequence[str],
    ) -> Sequence[str]: ...

    def confirm(
        self,
        prompt: str,
        default: bool = True,
    ) -> bool: ...

    def show_summary(
        self,
        fields: dict[str, str],
    ) -> None: ...

    def info(self, message: str) -> None: ...

    def success(self, message: str) -> None: ...

    def warning(self, message: str) -> None: ...

    def progress(self, message: str) -> None:
        """Notify that a long-running operation is starting."""

    def error(self, message: str) -> None: ...


# --- Filesystem & project layout -------------------------------------------


class FileSystemPort(Protocol):
    """Project filesystem operations required by application use cases."""

    def exists(self, path: str) -> bool: ...

    def is_dir(self, path: str) -> bool: ...

    def resolve(self, relative_path: str) -> str:
        """Resolve a project-relative path to an absolute path."""

    def make_directory(self, relative_path: str) -> None: ...

    def remove_tree(self, relative_path: str) -> None: ...

    def empty_directory(self, relative_path: str) -> None:
        """Delete a directory's contents while preserving the directory."""

    def write_text(
        self,
        relative_path: str,
        content: str,
    ) -> None: ...

    def read_text(self, relative_path: str) -> str: ...

    def copy_tree(
        self,
        source: Path,
        destination: Path,
    ) -> None: ...

    def current_user(self) -> str: ...

    def render_tree(self, root: str, variables: dict[str, object], exclude: Sequence[str] | None = None) -> None: ...


class ProjectScaffolderPort(Protocol):
    """Materializes a project from a template."""

    def create_project(self, config: ProjectConfig) -> None: ...


class ComponentWriterPort(Protocol):
    """Renders and writes generated components/views."""

    def render(self, spec: ComponentSpec) -> str:
        """Produce component source code."""

    def target_exists(self, spec: ComponentSpec) -> bool: ...

    def write(
        self,
        spec: ComponentSpec,
        code: str,
    ) -> str:
        """Write generated code and return its destination directory."""


# --- Templates --------------------------------------------------------------


class TemplateProviderPort(Protocol):
    def resolve_template(
        self,
        binding: Binding,
        target_platform: TargetPlatform,
        version: Version | None = None,
    ) -> Path: ...


# --- Settings ---------------------------------------------------------------


class SettingsPort(Protocol):
    """Access to project configuration and build settings."""

    def get(self, key: str) -> Any:
        """Return a required setting or raise MissingSettingError."""

    def get_optional(
        self,
        key: str,
        default: Any = None,
    ) -> Any: ...

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Update an in-memory setting."""

    def persist_base(
        self,
        values: dict[str, object],
    ) -> None:
        """Persist values to base project settings."""

    def activate_profile(self, profile: str) -> None: ...

    @property
    def base_settings_path(self) -> str: ...


class PackageMetadataPort(Protocol):
    """Provides metadata about the installed Qyro package."""

    def qyro_version(self) -> str: ...


# --- Dependencies & packages -----------------------------------------------

class DependencyInstallerPort(Protocol):
    """Installs dependencies declared by a project."""

    def install(self, project_dir: str) -> None: ...

class ImportlibModuleRegistry:
    """Checks whether Python modules are installed."""
    def is_installed(self, module_name: str) -> bool: ...

# --- Processes & application execution -------------------------------------


class ProcessRunnerPort(Protocol):
    """Runs external processes without exposing subprocess to the application."""

    def run(
        self,
        command: Sequence[str],
        env: Optional[dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> int: ...


class AppRunnerPort(Protocol):
    """Runs the user's application from source."""

    def run_from_source(
        self,
        main_module_path: str,
        source_root: str,
    ) -> int: ...


class TestRunnerPort(Protocol):
    """Runs the project's test suite."""

    def run(
        self,
        source_root: str,
        test_directories: Sequence[str],
    ) -> bool:
        """Return False when no tests were found."""


# --- Repository / upload ----------------------------------------------------


class UploaderPort(Protocol):
    """Uploads the project repository/package to the configured service."""

    def upload_repository(
        self,
        username: str,
        password: str,
    ) -> None: ...


# --- Platform strategies ----------------------------------------------------


class PlatformPort(Protocol):
    """
    Platform-specific operations.

    Implementations live in infrastructure. The application layer only
    depends on this abstraction and never checks the operating system itself.
    """

    @property
    def name(self) -> str: ...

    # Freeze ---------------------------------------------------------------

    def freeze(
        self,
        app_name: str,
        debug: bool,
    ) -> FreezeResult: ...

    # Code signing ---------------------------------------------------------

    def supports_signing(self) -> bool: ...

    def sign_app(self) -> Optional[str]:
        """Sign the frozen application and return a human-readable detail."""

    def has_codesigning_certificate(self) -> bool: ...

    # Installer ------------------------------------------------------------

    def create_installer(
        self,
        app_name: str,
        installer_file: str,
        user_level: bool,
    ) -> InstallerResult: ...

    def supports_signing_installer(self) -> bool: ...

    def sign_installer(self) -> None: ...

    # Repository -----------------------------------------------------------

    def supports_repo(self) -> bool: ...

    def create_repo(
        self,
        app_name: str,
        gpg_key: str,
    ) -> RepoResult: ...

    # Upload ---------------------------------------------------------------

    def upload_instructions(
        self,
        app_name: str,
        base_url: str,
        installer_url: str,
        repo_url: str,
        gpg_key: str,
    ) -> UploadResult: ...

    # General instructions -------------------------------------------------

    def get_instructions(self) -> str: ...

class ProgressPort(Protocol):
    def start(
        self,
        message: str,
        total: int | None = None,
    ) -> None:
        ...

    def update(self, completed: int) -> None:
        ...

    def stop(self) -> None:
        ...


class MobileBuildPort(Protocol):
    """
    !EXPERIMENTAL: This module is just for defining mobile target specifications for Android and iOS

    !#########################
    ! AVOID USING THIS MODULE
    !#########################


    Builds a project for a supported mobile target.
    """

    def init_spec(
        self,
        target: MobileTarget,
        config: ProjectConfig,
    ) -> None: ...

    def compile(
        self,
        target: MobileTarget,
        debug: bool,
    ) -> str: ...