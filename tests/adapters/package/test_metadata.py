
from unittest.mock import patch

from qyro.adapters.package.metadata import PackageMetadata


@patch("qyro.adapters.package.metadata.version")
def test_qyro_version(mock_version):
    mock_version.return_value = "1.2.3"

    metadata = PackageMetadata()

    result = metadata.qyro_version()

    assert result == "1.2.3"
    mock_version.assert_called_once_with("qyro")
