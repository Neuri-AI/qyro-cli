"""
qyro.application.use_cases.freeze
Orchestrates freezing desktop applications following Clean Architecture principles.
Supports build.json manifests, settings/base.json, platform-specific JSONs,
UAC elevation, onefile/onedir modes, debug flags, performance optimizations,
and bindings (PyQt5/6, PySide6/2, Kivy, Tkinter).
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from qyro.application.ports import (
    BinaryOptimizerPort,
    FreezerPort,
    SettingsPort,
    UserInteractionPort,
)
from qyro.domain.build import (
    BuildArtifact,
    BundleMode,
    DebugConfig,
    FreezeManifest,
    KivyConfig,
    OptimizationConfig,
    UACConfig,
    UACLevel,
)
from qyro.domain.errors import QyroError


class FreezeDesktopUseCase:
    """
    Main use case for building and freezing desktop executables.
    Merges configuration hierarchically:
    1. settings/base.json
    2. settings/<platform>.json or settings/release.json
    3. build.json (or custom manifest)
    4. CLI argument overrides (--debug, --onefile, --uac, etc.)
    """

    def __init__(
        self,
        freezer: FreezerPort,
        settings_repo: SettingsPort,
        optimizer: BinaryOptimizerPort,
        ui: UserInteractionPort,
    ):
        self._freezer = freezer
        self._settings = settings_repo
        self._optimizer = optimizer
        self._ui = ui

    def execute(
        self,
        project_root: Optional[Path] = None,
        bundle: Optional[str] = None,
        profile: str = "release",
        debug: Optional[bool] = None,
        uac: Optional[bool] = None,
        clean: Optional[bool] = None,
        extra_args: Optional[List[str]] = None,
        interactive: bool = False,
    ) -> BuildArtifact:
        root = (project_root or Path.cwd()).resolve()

        # Step 1: Detect Host / Target Platform
        current_platform = self._detect_platform()

        # Step 2: Activate platform and profile in SettingsPort if supported
        if hasattr(self._settings, "activate_profile"):
            self._settings.activate_profile(current_platform)
            if profile and profile.lower() != current_platform:
                self._settings.activate_profile(profile)

        # Step 3: Parse and merge settings and build.json
        manifest = self._load_manifest(
            root=root,
            platform_name=current_platform,
            cli_bundle=bundle,
            cli_debug=debug,
            cli_uac=uac,
            cli_clean=clean,
        )

        # Step 4: Validate manifest
        manifest.validate()

        # Step 5: Interactive confirmation if requested
        if interactive:
            self._show_interactive_review(manifest)

        # Step 6: Inform user
        self._ui.info(
            f"🚀 [bold #ff8c00]Qyro Freeze[/bold #ff8c00] :: Preparing binary for "
            f"[bold #fff]{manifest.app_name}[/bold #fff] ({manifest.target_platform})"
        )

        # Step 7: Execute Freezing via FreezerPort
        artifact = self._freezer.freeze(
            project_root=root,
            manifest=manifest,
            extra_args=extra_args,
        )

        # Step 8: Apply binary optimizations (UPX, stripping)
        self._optimizer.optimize(artifact, manifest.optimization)

        # Step 9: Report results cleanly
        self._report_success(artifact)

        return artifact

    def _detect_platform(self) -> str:
        if sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("darwin"):
            return "mac"
        return "linux"

    def _load_manifest(
        self,
        root: Path,
        platform_name: str,
        cli_bundle: Optional[str],
        cli_debug: Optional[bool],
        cli_uac: Optional[bool],
        cli_clean: Optional[bool] = None,
    ) -> FreezeManifest:
        # Load from build.json if present
        build_json_path = root / "build.json"
        build_data: Dict[str, Any] = {}
        if build_json_path.exists():
            try:
                build_data = json.loads(build_json_path.read_text(encoding="utf-8"))
            except Exception as e:
                self._ui.warning(f"Failed to parse build.json: {e}")

        # Base properties with fallback to settings
        app_name = (
            build_data.get("app_name")
            or self._settings.get_optional("app_name", root.name)
        )
        author = (
            build_data.get("author")
            or self._settings.get_optional("author", "Developer")
        )
        version = (
            build_data.get("version")
            or self._settings.get_optional("version", "1.0.0")
        )
        entry_point = (
            build_data.get("entry_point")
            or self._settings.get_optional("entry_point", "main.py")
        )
        binding = (
            build_data.get("binding")
            or self._settings.get_optional("binding", "PySide6")
        )

        # Target platform
        target_platform = build_data.get("platform", platform_name)

        # Bundle mode (CLI overrides JSON and settings)
        bundle_str = (
            cli_bundle
            or build_data.get("bundle")
            or build_data.get("bundle_mode")
            or self._settings.get_optional("bundle_mode")
            or self._settings.get_optional("bundle", "onedir")
        )
        bundle_mode = BundleMode.parse(bundle_str)

        # UAC Config (checks build_data first, then settings/<platform>.json)
        uac_raw = build_data.get("uac") or self._settings.get_optional("uac", {})
        if isinstance(uac_raw, bool):
            uac_level = UACLevel.REQUIRE_ADMINISTRATOR if uac_raw else UACLevel.AS_INVOKER
            uac_uiaccess = False
        elif isinstance(uac_raw, dict):
            uac_level = UACLevel.parse(uac_raw.get("level", "asInvoker"))
            uac_uiaccess = bool(uac_raw.get("ui_access", False))
        else:
            uac_level = UACLevel.AS_INVOKER
            uac_uiaccess = False

        if cli_uac is not None:
            uac_level = UACLevel.REQUIRE_ADMINISTRATOR if cli_uac else UACLevel.AS_INVOKER

        uac_config = UACConfig(level=uac_level, ui_access=uac_uiaccess)

        # Debug Config (checks build_data first, then settings/<platform>.json)
        debug_raw = build_data.get("debug") or self._settings.get_optional("debug", {})
        if isinstance(debug_raw, bool):
            dbg_enabled = debug_raw
            dbg_console = debug_raw
            dbg_unstripped = False
            dbg_bootloader = False
        elif isinstance(debug_raw, dict):
            dbg_enabled = bool(debug_raw.get("enabled", False))
            dbg_console = bool(debug_raw.get("console", False))
            dbg_unstripped = bool(debug_raw.get("unstripped", False))
            dbg_bootloader = bool(debug_raw.get("bootloader_debug", False))
        else:
            dbg_enabled = False
            dbg_console = False
            dbg_unstripped = False
            dbg_bootloader = False

        if cli_debug is not None:
            dbg_enabled = cli_debug
            dbg_console = cli_debug

        debug_config = DebugConfig(
            enabled=dbg_enabled,
            console_window=dbg_console,
            unstripped=dbg_unstripped,
            bootloader_debug=dbg_bootloader,
        )

        # Optimization Config (checks build_data first, then settings/<platform>.json)
        opt_raw = build_data.get("optimization") or self._settings.get_optional("optimization", {})
        clean_build = (
            cli_clean
            if cli_clean is not None
            else bool(opt_raw.get("clean_build", True))
        )
        opt_config = OptimizationConfig(
            upx_enabled=bool(opt_raw.get("upx_enabled", True)),
            upx_level=int(opt_raw.get("upx_level", 9)),
            upx_excludes=opt_raw.get("upx_excludes", [
                "vcruntime140.dll", "python3*.dll", "sdl2.dll", "glew32.dll", "kivy*.pyd"
            ]),
            bytecode_opt=int(opt_raw.get("bytecode_opt", 1)),
            strip_binaries=bool(opt_raw.get("strip_binaries", True)),
            exclude_modules=opt_raw.get("exclude_modules", ["unittest", "test", "pydoc"]),
            clean_build=clean_build,
        )

        # Hidden imports and resources
        hidden_imports = list(build_data.get("hidden_imports", []))
        base_hidden = self._settings.get_optional("hidden_imports", [])
        if isinstance(base_hidden, list):
            hidden_imports.extend(base_hidden)
        # Deduplicate while preserving order
        dedup_hidden = list(dict.fromkeys(hidden_imports))

        icon_path = build_data.get("icon") or self._settings.get_optional("icon", None)
        extra_args = build_data.get("extra_args", [])

        return FreezeManifest(
            app_name=app_name,
            author=author,
            version=version,
            entry_point=entry_point,
            target_platform=target_platform,
            bundle_mode=bundle_mode,
            binding=binding,
            icon_path=icon_path,
            uac=uac_config,
            debug=debug_config,
            optimization=opt_config,
            hidden_imports=dedup_hidden,
            extra_pyinstaller_args=extra_args,
        )

    def _show_interactive_review(self, manifest: FreezeManifest) -> None:
        fields = {
            "Application": manifest.app_name,
            "Target OS": manifest.target_platform,
            "GUI Binding": manifest.binding,
            "Entry Point": manifest.entry_point,
            "Bundle Format": manifest.bundle_mode.value.upper(),
            "Debug Mode": "ENABLED (Console open)" if manifest.debug.enabled else "Disabled (Windowed)",
            "Windows UAC": manifest.uac.level.value,
            "UPX Compression": f"Level {manifest.optimization.upx_level}" if manifest.optimization.upx_enabled else "Disabled",
        }
        self._ui.show_summary("Freeze Configuration Review", fields)
        if not self._ui.confirm("Proceed with build?", default=True):
            self._ui.info("Build cancelled by user.")
            sys.exit(0)

    def _report_success(self, artifact: BuildArtifact) -> None:
        size_mb = artifact.size_bytes / (1024 * 1024)
        self._ui.success("\n✨ [bold green]Application frozen successfully![/bold green]")
        self._ui.info(f"  • [bold]Output Location:[/bold] [#fdba74]{artifact.output_dir}[/#fdba74]")
        self._ui.info(f"  • [bold]Executable:[/bold] [#fdba74]{artifact.executable_path.name}[/#fdba74]")
        self._ui.info(f"  • [bold]Size:[/bold] {size_mb:.2f} MB ({artifact.size_bytes:,} bytes)")
        self._ui.info(f"  • [bold]Duration:[/bold] {artifact.duration_seconds:.2f}s")
        if artifact.uac_applied:
            self._ui.info("  • [bold]UAC Manifest:[/bold] Administrator Privilege Elevation Enabled (requireAdministrator)")
        if artifact.debug_mode:
            self._ui.info("  • [bold]Debug:[/bold] Active console attached for stdout/stderr debugging")
