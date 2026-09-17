"""
qyro.application.use_cases.init_project
Orchestrates project initialization following Clean Architecture.
"""

import json
from pathlib import Path

from qyro.application.ports import (
    FileSystemPort,
    SettingsPort,
    TemplateProviderPort,
    UserInteractionPort,
    DependencyInstallerPort,
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
        dependencies: DependencyInstallerPort,
        templates: TemplateProviderPort,
        settings_repo: SettingsPort,
    ):
        self.ui = ui
        self.fs = fs
        self.dependencies = dependencies
        self.templates = templates
        self.settings = settings_repo

    def execute(
        self,
        target_dir: str = ".",
        default_binding: str | None = None,
        template_version: str | None = None,
    ) -> None:
        destination = Path(target_dir).resolve()
        src_path = destination / "main.py"

        if self.fs.exists(str(src_path)):
            raise ProjectAlreadyExistsError(str(destination))

        self.ui.welcome()

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

        if default_binding:
            binding = Binding.parse(default_binding)

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
            default=self.fs.current_user(),
        )

        addon_options = {
            "Hot Reloading (⚠️ Experimental)": AddonModule.HOTRL,
            "Pydux (Redux-style State Management)": AddonModule.PYDUX,
            "Sentry (Crash Reporting Integration)": AddonModule.SENTRY,
            "Requests (HTTP Library)": AddonModule.REQUESTS,
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

        self.fs.render_tree(
            str(destination),
            {
                **config.as_template_variables(),
                **config.as_base_settings(),
            },
        )

        self.ui.info("Installing project dependencies...")
        self.dependencies.install(str(destination))

        self.ui.success(
            f"\n✓ Project initialized successfully in "
            f"[bold #ff8c00]{target_dir}/[/bold #ff8c00]"
        )
        self.ui.info("\nNext steps:")

        if target_dir != ".":
            self.ui.info(
                f"  [bold #ff8c00]cd {target_dir}[/bold #ff8c00]"
            )

        self.ui.info(
            "  [bold #ff8c00]qyro start[/bold #ff8c00]"
        )
