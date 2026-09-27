from pathlib import Path

from qyro.adapters.freeze.framework_hooks import FrameworkHookResolver
from qyro.adapters.freeze.pyinstaller_adapter import PyInstallerFreezer
from qyro.domain.build import FreezeManifest


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
    assert "--collect-binaries" in args
    assert "PySide2" in args[args.index("--collect-binaries") + 1]
    assert "--collect-data" in args
    assert "PySide2" in args[args.index("--collect-data") + 1]


def test_build_command_includes_windows_qt_runtime_paths(tmp_path):
    project_root = tmp_path
    (project_root / "main.py").write_text("print('hello')\n", encoding="utf-8")

    freezer = PyInstallerFreezer(FrameworkHookResolver())
    manifest = FreezeManifest(
        app_name="MyApp",
        binding="PySide2",
        entry_point="main.py",
        target_platform="windows",
    )

    cmd = freezer.build_command(project_root, manifest)

    assert "--paths" in cmd
    assert any(arg.endswith("Library\\bin") or arg.endswith("Library/bin") for arg in cmd)
