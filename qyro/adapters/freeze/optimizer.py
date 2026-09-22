"""
qyro.adapters.freeze.optimizer
Binary optimization adapter implementing BinaryOptimizerPort.
Runs UPX executable compression if upx is present on PATH, and cleans up artifacts.
"""

import shutil
import subprocess
from pathlib import Path

from qyro.application.ports import BinaryOptimizerPort, UserInteractionPort
from qyro.domain.build import BuildArtifact, OptimizationConfig

class BinaryOptimizer(BinaryOptimizerPort):
    def __init__(self, ui: UserInteractionPort | None = None):
        self._ui = ui

    def optimize(
        self,
        artifact: BuildArtifact,
        config: OptimizationConfig,
    ) -> None:
        if config.strip_binaries:
            self._strip_binaries(artifact)

        if config.upx_enabled:
            self._compress_with_upx(artifact, config)

    def _strip_binaries(self, artifact: BuildArtifact) -> None:
        strip_bin = shutil.which("strip")

        if not strip_bin or not artifact.output_dir or not artifact.output_dir.exists():
            return

        stripped_count = 0

        for file_path in artifact.output_dir.rglob("*"):
            if not self._is_strippable_binary(file_path):
                continue

            try:
                subprocess.run(
                    [strip_bin, "--strip-unneeded", str(file_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                stripped_count += 1
            except Exception:
                continue

        if stripped_count and self._ui:
            self._ui.info(
                f"✓ Stripped unneeded debug symbols from {stripped_count} binary files."
            )

    @staticmethod
    def _is_strippable_binary(file_path: Path) -> bool:
        if not file_path.is_file() or file_path.is_symlink():
            return False

        return (
            file_path.suffix in (".so", ".dylib")
            or ".so." in file_path.name
        )

    def _compress_with_upx(
        self,
        artifact: BuildArtifact,
        config: OptimizationConfig,
    ) -> None:
        upx_bin = shutil.which("upx")

        if not upx_bin or not artifact.executable_path.exists():
            return

        try:
            result = subprocess.run(
                [
                    upx_bin,
                    f"-{config.upx_level}",
                    str(artifact.executable_path),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if result.returncode == 0 and self._ui:
                self._ui.info("✓ UPX binary compression successfully applied.")
        except Exception:
            pass