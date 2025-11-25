from copy import deepcopy
import pytest
from unittest.mock import patch

from quam.core import *


@pytest.fixture
def BareQuamRoot():
    @quam_dataclass
    class BareQuamRoot(QuamRoot): ...

    return BareQuamRoot


@pytest.fixture
def BareQuamComponent():
    @quam_dataclass
    class BareQuamComponent(QuamComponent): ...

    return BareQuamComponent


@pytest.fixture(scope="function", autouse=True)
def remove_quam_root():
    from quam.core import QuamBase

    QuamBase._last_instantiated_root = None


@pytest.fixture
def qua_config():
    from quam.core.qua_config_template import qua_config_template

    return deepcopy(qua_config_template)


@pytest.fixture(scope="function", autouse=True)
def mock_quam_config():
    """Mock get_quam_config to prevent loading system config during tests."""
    with patch('quam.core.quam_classes.get_quam_config') as mock:
        mock.side_effect = FileNotFoundError("No config file in test environment")
        yield mock
