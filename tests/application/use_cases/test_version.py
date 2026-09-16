
from unittest.mock import Mock

from qyro.application.use_cases.version import ShowVersionUseCase


class TestShowVersionUseCase:
    def test_execute_displays_qyro_version(self):
        ui = Mock()
        metadata = Mock()

        metadata.qyro_version.return_value = "1.2.3"

        use_case = ShowVersionUseCase(
            ui=ui,
            metadata=metadata,
        )

        result = use_case.execute()

        assert result is None
        metadata.qyro_version.assert_called_once_with()
        ui.info.assert_called_once_with("Qyro v1.2.3")
