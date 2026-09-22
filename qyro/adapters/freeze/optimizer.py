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
        if not config.upx_enabled:
            return

        upx_bin = shutil.which("upx")
        if not upx_bin:
            return

        if not artifact.executable_path.exists():
            return

        # Run UPX on generated executable
        cmd = [
            upx_bin,
            f"-{config.upx_level}",
            str(artifact.executable_path),
        ]

        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if res.returncode == 0 and self._ui:
                self._ui.info("✓ UPX binary compression successfully applied.")
        except Exception:
            pass
