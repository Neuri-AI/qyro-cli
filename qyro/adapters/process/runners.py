"""Subprocess, importlib, unittest and upload adapters."""

import os
import subprocess
import sys
from importlib.util import find_spec
from os.path import isfile, join
from typing import List
from unittest import TestSuite, TextTestRunner, defaultTestLoader

from qyro.domain.errors import PackageInstallationError


class ImportlibModuleRegistry:
    """ModuleRegistryPort — replaces the old `_has_module`."""

    def is_installed(self, module_name: str) -> bool:
        try:
            return bool(find_spec(module_name))
        except (ImportError, ValueError):
            return False


class PipPackageInstaller:
    """PackageInstallerPort."""

    def install(self, package: str) -> None:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
            )
        except subprocess.CalledProcessError:
            raise PackageInstallationError(package) from None


class SubprocessAppRunner:
    """AppRunnerPort — runs the user's app with src/main/python on the path."""

    def run_from_source(
        self,
        main_module_path: str,
        source_root: str,
    ) -> int:
        env = dict(os.environ)
        existing = env.get("PYTHONPATH", "")

        env["PYTHONPATH"] = (
            source_root + os.pathsep + existing
            if existing
            else source_root
        )

        completed = subprocess.run(
            [sys.executable, main_module_path],
            env=env,
        )

        return completed.returncode


class UnittestRunner:
    """TestRunnerPort. Returns False when there was nothing to run."""

    def run(self, source_root: str, test_directories: List[str]) -> bool:
        sys.path.append(source_root)
        suite = TestSuite()
        for test_dir in test_directories:
            sys.path.append(test_dir)
            try:
                entries = os.listdir(test_dir)
            except FileNotFoundError:
                continue
            for entry in entries:
                if isfile(join(test_dir, entry, "__init__.py")):
                    suite.addTest(
                        defaultTestLoader.discover(
                            entry, top_level_dir=test_dir)
                    )
        if not list(suite):
            return False
        TextTestRunner().run(suite)
        return True


class QyroUploader:
    """UploaderPort."""

    def upload_repository(self, username: str, password: str) -> None:
        from qyro.upload import _upload_repo
        _upload_repo(username, password)
