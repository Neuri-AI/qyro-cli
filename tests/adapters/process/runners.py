import os
import subprocess
import sys
from unittest import mock

import pytest

from qyro.adapters.process.runners import (
    ImportlibModuleRegistry,
    PipPackageInstaller,
    QyroUploader,
    SubprocessAppRunner,
    UnittestRunner,
)
from qyro.domain.errors import PackageInstallationError


class TestImportlibModuleRegistry:
    def test_is_installed_returns_true_for_installed_module(self):
        registry = ImportlibModuleRegistry()

        assert registry.is_installed("json") is True

    def test_is_installed_returns_false_for_missing_module(self):
        registry = ImportlibModuleRegistry()

        assert registry.is_installed("module_that_does_not_exist") is False

    def test_is_installed_returns_false_when_find_spec_raises_import_error(
        self,
    ):
        registry = ImportlibModuleRegistry()

        with mock.patch(
            "qyro.adapters.process.runners.find_spec",
            side_effect=ImportError,
        ):
            assert registry.is_installed("example") is False

    def test_is_installed_returns_false_when_find_spec_raises_value_error(
        self,
    ):
        registry = ImportlibModuleRegistry()

        with mock.patch(
            "qyro.adapters.process.runners.find_spec",
            side_effect=ValueError,
        ):
            assert registry.is_installed("example") is False


class TestPipPackageInstaller:
    def test_install_runs_pip_with_current_python(self):
        installer = PipPackageInstaller()

        with mock.patch(
            "qyro.adapters.process.runners.subprocess.run"
        ) as run:
            installer.install("requests")

        run.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "requests"],
            check=True,
        )

    def test_install_raises_package_installation_error_on_failure(self):
        installer = PipPackageInstaller()

        with mock.patch(
            "qyro.adapters.process.runners.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, ["pip"]),
        ):
            with pytest.raises(PackageInstallationError):
                installer.install("invalid-package")


class TestSubprocessAppRunner:
    def test_run_from_source_sets_pythonpath(self, monkeypatch):
        runner = SubprocessAppRunner()
        monkeypatch.setenv("PYTHONPATH", "existing/path")

        with mock.patch(
            "qyro.adapters.process.runners.subprocess.run"
        ) as run:
            run.return_value.returncode = 0

            result = runner.run_from_source(
                "src/main.py",
                "src",
            )

        assert result == 0

        run.assert_called_once()
        args, kwargs = run.call_args

        assert args[0] == [sys.executable, "src/main.py"]
        assert kwargs["env"]["PYTHONPATH"] == (
            "src" + os.pathsep + "existing/path"
        )

    def test_run_from_source_sets_pythonpath_when_none_exists(
        self,
        monkeypatch,
    ):
        runner = SubprocessAppRunner()
        monkeypatch.delenv("PYTHONPATH", raising=False)

        with mock.patch(
            "qyro.adapters.process.runners.subprocess.run"
        ) as run:
            run.return_value.returncode = 7

            result = runner.run_from_source(
                "main.py",
                "src",
            )

        assert result == 7

        kwargs = run.call_args.kwargs
        assert kwargs["env"]["PYTHONPATH"] == "src"

    def test_run_from_source_returns_process_exit_code(self):
        runner = SubprocessAppRunner()

        with mock.patch(
            "qyro.adapters.process.runners.subprocess.run"
        ) as run:
            run.return_value.returncode = 42

            result = runner.run_from_source(
                "main.py",
                "src",
            )

        assert result == 42


class TestUnittestRunner:
    def test_run_returns_false_when_test_directory_does_not_exist(
        self,
        tmp_path,
    ):
        runner = UnittestRunner()

        result = runner.run(
            str(tmp_path),
            [str(tmp_path / "tests")],
        )

        assert result is False

    def test_run_returns_false_when_no_tests_are_discovered(
        self,
        tmp_path,
    ):
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        runner = UnittestRunner()

        with mock.patch(
            "qyro.adapters.process.runners.defaultTestLoader.discover"
        ) as discover:
            discover.return_value = mock.Mock()
            discover.return_value.__iter__ = mock.Mock(
                return_value=iter(())
            )

            result = runner.run(
                str(tmp_path),
                [str(test_dir)],
            )

        assert result is False

    def test_run_discovers_tests_and_runs_suite(self, tmp_path):
        test_dir = tmp_path / "tests"
        test_package = test_dir / "sample"
        test_package.mkdir(parents=True)
        (test_package / "__init__.py").write_text("")

        runner = UnittestRunner()

        discovered_test = mock.Mock()

        with mock.patch(
            "qyro.adapters.process.runners.defaultTestLoader.discover",
            return_value=discovered_test,
        ) as discover, mock.patch(
            "qyro.adapters.process.runners.TextTestRunner.run"
        ) as test_runner_run:
            result = runner.run(
                str(tmp_path),
                [str(test_dir)],
            )

        assert result is True

        discover.assert_called_once_with(
            "sample",
            top_level_dir=str(test_dir),
        )
        test_runner_run.assert_called_once()

    def test_run_adds_source_root_to_sys_path(
        self,
        tmp_path,
        monkeypatch,
    ):
        runner = UnittestRunner()

        original_path = list(sys.path)

        try:
            runner.run(
                str(tmp_path),
                [str(tmp_path / "missing")],
            )

            assert str(tmp_path) in sys.path
        finally:
            sys.path[:] = original_path

    def test_run_adds_test_directories_to_sys_path(
        self,
        tmp_path,
    ):
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        runner = UnittestRunner()

        original_path = list(sys.path)

        try:
            runner.run(
                str(tmp_path),
                [str(test_dir)],
            )

            assert str(test_dir) in sys.path
        finally:
            sys.path[:] = original_path


class TestQyroUploader:
    def test_upload_repository_calls_upload_repo(self):
        uploader = QyroUploader()

        upload_repo = mock.Mock()

        fake_module = mock.Mock()
        fake_module._upload_repo = upload_repo

        with mock.patch.dict(
            sys.modules,
            {"qyro.upload": fake_module},
        ):
            uploader.upload_repository(
                "username",
                "password",
            )

        upload_repo.assert_called_once_with(
            "username",
            "password",
        )