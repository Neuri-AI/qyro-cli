"""
qyro.application.use_cases.init_project
Orchestrates project initialization following Clean Architecture.
"""

import json
from pathlib import Path

from qyro.application.ports import (
    FileSystemPort,
    ModuleRegistryPort,
    PackageInstallerPort,
    SettingsPort,
    TemplateProviderPort,
    UserInteractionPort,
)
from qyro.domain.errors import ProjectAlreadyExistsError
from qyro.domain.project import (
    AddonModule,
    Binding,
    ProjectConfig,
    TargetPlatform,
)
from qyro.domain.version import Version


class InitProjectUseCase:
    def __init__(
        self,
        ui: UserInteractionPort,
        fs: FileSystemPort,
        modules: ModuleRegistryPort,
        installer: PackageInstallerPort,
        templates: TemplateProviderPort,
        settings_repo: SettingsPort,
    ):
        self.ui = ui
        self.fs = fs
        self.modules = modules
        self.installer = installer
        self.templates = templates
        self.settings = settings_repo

    def execute(
        self,
        target_dir: str = ".",
        preselected_binding: str | None = None,
        template_version: str | None = None,
    ) -> None:
        destination = Path(target_dir).resolve()
        src_path = destination / "src"

        if self.fs.exists(str(src_path)):
            raise ProjectAlreadyExistsError(str(destination))

        self.ui.info(
            "✨ Welcome to "
            "[bold green]Qyro Engine Project Generator[/bold green] ✨\n"
        )

        platform_options = {
            "iPhone": TargetPlatform.IPHONE,
            "Android": TargetPlatform.ANDROID,
            "Desktop (x86)": TargetPlatform.X86,
            "Desktop (Apple Silicon)": TargetPlatform.APPLE_SILICON,
        }

        platform_str = self.ui.ask_choice(
            "Select target platform",
            list(platform_options),
            default="Desktop (x86)",
        )

        target_platform = platform_options[platform_str]

        available_bindings = [
            binding
            for binding in Binding
            if binding.supports(target_platform)
        ]

        if preselected_binding:
            binding = Binding.parse(preselected_binding)

            if binding not in available_bindings:
                raise ValueError(
                    f"Binding '{binding.value}' is not available "
                    f"for {target_platform.value}."
                )
        else:
            binding_str = self.ui.ask_choice(
                "Select UI binding",
                [binding.value for binding in available_bindings],
                default="PySide6",
            )
            binding = Binding.parse(binding_str)

        default_app = destination.name if target_dir != "." else "MyApp"
        app_name = self.ui.ask_text(
            "App name",
            default=default_app,
        )

        version_str = self.ui.ask_text(
            "Version",
            default="1.0.0",
        )
        version = Version.parse(version_str)

        author = self.ui.ask_text(
            "Author",
            default=self.fs.default_author(),
        )

        addon_options = {
            "Hot Reloading (⚠️ Experimental)": AddonModule.HOTRL,
            "Pydux (Redux-style State Management)": AddonModule.PYDUX,
            "Sentry (Crash Reporting Integration)": AddonModule.SENTRY,
        }

        if target_platform in (
            TargetPlatform.IPHONE,
            TargetPlatform.ANDROID,
        ):
            addon_options = {
                "Pydux (Redux-style State Management)": AddonModule.PYDUX,
            }

        selected_addons_raw = self.ui.ask_multi_choice(
            "Select optional add-ons to configure:",
            list(addon_options),
        )

        addons = [
            addon_options[option]
            for option in selected_addons_raw
            if option in addon_options
        ]

        bundle_id = None

        if target_platform in (
            TargetPlatform.IPHONE,
            TargetPlatform.APPLE_SILICON,
        ):
            bundle_default = (
                f"com.{author.lower().split()[0]}."
                f"{''.join(app_name.lower().split())}"
            )

            label = (
                "iOS bundle identifier"
                if target_platform == TargetPlatform.IPHONE
                else f"Mac bundle identifier (e.g. {bundle_default}, optional)"
            )

            bundle_id = self.ui.ask_text(
                label,
                default=bundle_default,
                show_default=target_platform == TargetPlatform.IPHONE,
            )

            if (
                target_platform == TargetPlatform.APPLE_SILICON
                and not bundle_id.strip()
            ):
                bundle_id = None

        config = ProjectConfig(
            app_name=app_name,
            version=version,
            author=author,
            binding=binding,
            target_platform=target_platform,
            mac_bundle_identifier=bundle_id or None,
            addons=addons,
        )

        self.ui.show_summary(
            "Please Confirm",
            config.as_display_dict(),
        )

        if not self.ui.confirm(
            "Create project with these settings?"
        ):
            self.ui.info("Operation aborted by user.")
            return

        if not self.modules.is_installed(config.binding.value):
            self.ui.info(
                f"Installing [cyan]{config.binding.value}[/cyan]..."
            )
            self.installer.install(config.binding.value)

        for addon in config.addons:
            if not self.modules.is_installed(addon.value):
                self.ui.info(
                    f"Installing add-on [cyan]{addon.value}[/cyan]..."
                )
                self.installer.install(addon.value)

        self.ui.info("Resolving boilerplate template...")
        template_dir = self.templates.resolve_template(
            binding=config.binding,
            target_platform=config.target_platform,
            version=(
                Version.parse(template_version)
                if template_version
                else None
            ),
        )

        self.fs.copy_tree(
            template_dir,
            destination,
        )

        """self.fs.write_file(
            str(destination / "src" / "build" / "base.json"),
            json.dumps(
                config.as_base_settings(),
                indent=2,
            ),
        )"""

        self.ui.success(
            f"\n🎉 Project initialized successfully in "
            f"[bold cyan]{target_dir}[/bold cyan]!"
        )
        self.ui.info(
            "Run:\n    [bold green]qyro start[/bold green]\n"
        )
