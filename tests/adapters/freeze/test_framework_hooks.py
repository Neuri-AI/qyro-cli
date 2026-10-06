from pathlib import Path

from qyro_cli.adapters.freeze.framework_hooks import FrameworkHookResolver
from qyro_cli.adapters.freeze.pyinstaller_adapter import PyInstallerFreezer
from qyro_cli.domain.build import FreezeManifest


def test_pyside2_collects_runtime_binaries_and_data():
    resolver = FrameworkHookResolver()
    manifest = FreezeManifest(
        app_name="MyApp",
        binding="PySide2",
        entry_point="main.py",
        target_platform="windows",
    )

    args = resolver.resolve_args(Path("."), manifest)

    assert "--collect-all" in args
    assert "PySide2" in args[args.index("--collect-all") + 1]
    assert "shiboken2" in args


def test_build_command_includes_windows_qt_runtime_paths(tmp_path):
    project_root = tmp_path
    (project_root / "main.py").write_text("print('hello')\n", encoding="utf-8")
    settings_dir = project_root / "settings"
    settings_dir.mkdir(parents=True)
    (settings_dir / "base.json").write_text('{"app_name":"MyApp"}', encoding="utf-8")
    (settings_dir / "secrets.json").write_text('{"token":"x"}', encoding="utf-8")

    freezer = PyInstallerFreezer(FrameworkHookResolver())
    manifest = FreezeManifest(
        app_name="MyApp",
        binding="PySide2",
        entry_point="main.py",
        target_platform="windows",
    )

    cmd = freezer.build_command(project_root, manifest)

    assert "--collect-all" in cmd
    assert "PySide2" in cmd


def test_framework_hooks_skip_plain_assets_when_protection_enabled(tmp_path):
    project_root = tmp_path
    settings_dir = project_root / "settings"
    resources_dir = project_root / "resources"
    settings_dir.mkdir(parents=True)
    resources_dir.mkdir(parents=True)
    (settings_dir / "base.json").write_text("{}", encoding="utf-8")
    (resources_dir / "logo.png").write_text("bin", encoding="utf-8")

    resolver = FrameworkHookResolver()
    manifest = FreezeManifest(
        app_name="MyApp",
        binding="PySide2",
        entry_point="main.py",
        target_platform="windows",
        protect_resources=True,
    )

    args = resolver.resolve_args(project_root, manifest)

    add_data_values = [args[i + 1] for i, token in enumerate(args) if token == "--add-data"]
    assert not any(value.endswith(":settings") or value.endswith(";settings") for value in add_data_values)
    assert not any(value.endswith(":resources") or value.endswith(";resources") for value in add_data_values)


def test_framework_hooks_exclude_local_secret_and_signing_files(tmp_path):
    project_root = tmp_path
    settings_dir = project_root / "settings"
    resources_dir = project_root / "resources"
    settings_dir.mkdir(parents=True)
    resources_dir.mkdir(parents=True)
    (settings_dir / "base.json").write_text("{}", encoding="utf-8")
    (settings_dir / "secrets.json").write_text('{"password":"local"}', encoding="utf-8")
    (settings_dir / "sign.json").write_text(
        '{"sign":{"windows":{"password":"signing-secret"}}}',
        encoding="utf-8",
    )
    (resources_dir / "logo.png").write_text("bin", encoding="utf-8")

    resolver = FrameworkHookResolver()
    manifest = FreezeManifest(
        app_name="MyApp",
        binding="PySide2",
        entry_point="main.py",
        target_platform="windows",
        protect_resources=False,
    )

    args = resolver.resolve_args(project_root, manifest)
    add_data_values = [args[i + 1] for i, token in enumerate(args) if token == "--add-data"]

    assert any("base.json" in value for value in add_data_values)
    assert not any("secrets.json" in value for value in add_data_values)
    assert not any("sign.json" in value for value in add_data_values)


def test_build_command_embeds_protected_bundle_and_runtime_module(tmp_path):
    project_root = tmp_path
    (project_root / "main.py").write_text("print('hello')\n", encoding="utf-8")
    settings_dir = project_root / "settings"
    resources_dir = project_root / "resources"
    settings_dir.mkdir(parents=True)
    resources_dir.mkdir(parents=True)
    (settings_dir / "base.json").write_text('{"app_name": "MyApp"}', encoding="utf-8")
    (settings_dir / "secrets.json").write_text('{"api": {"token": "local-secret"}}', encoding="utf-8")
    (resources_dir / "logo.png").write_text("png", encoding="utf-8")

    freezer = PyInstallerFreezer(FrameworkHookResolver())
    manifest = FreezeManifest(
        app_name="MyApp",
        binding="PySide2",
        entry_point="main.py",
        target_platform="windows",
        protect_resources=True,
    )

    cmd = freezer.build_command(project_root, manifest)

    pak_path = project_root / ".qyro" / "protected_resources.pak"
    external_secrets_path = project_root / ".qyro" / "secrets.json"
    runtime_dir = project_root / ".qyro"

    assert pak_path.exists()
    assert not external_secrets_path.exists()
    runtime_candidates = list(runtime_dir.glob("runtime*.so")) + list(runtime_dir.glob("runtime*.pyd"))
    assert runtime_candidates
    assert "--add-data" in cmd
    add_data_values = [cmd[i + 1] for i, token in enumerate(cmd) if token == "--add-data"]
    assert any(".qyro/protected_resources.pak" in value for value in add_data_values)
    assert any(".qyro/runtime" in value and (".so" in value or ".pyd" in value) for value in add_data_values)
    assert not any(".qyro/secrets.json" in value for value in add_data_values)


def test_copy_mac_resources_skips_plain_resources_when_protected(tmp_path):
    project_root = tmp_path
    app_bundle = project_root / "build" / "MyApp.app"
    resources_dest = app_bundle / "Contents" / "Resources"
    resources_dest.mkdir(parents=True)

    source = project_root / "resources" / "linux" / "icons"
    source.mkdir(parents=True)
    (source / "128.png").write_text("png", encoding="utf-8")

    freezer = PyInstallerFreezer(FrameworkHookResolver())
    manifest = FreezeManifest(
        app_name="MyApp",
        binding="PySide2",
        entry_point="main.py",
        target_platform="mac",
        protect_resources=True,
    )

    freezer._copy_mac_resources(project_root, app_bundle, manifest)

    assert not (resources_dest / "linux" / "icons" / "128.png").exists()
