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


@pytest.fixture(scope="session", autouse=True)
def prevent_default_config_loading():
    """
    Prevents loading ~/.qualibrate config during tests by changing the default
    config filename to a non-existent file.

    This ensures tests pass regardless of whether ~/.qualibrate exists on the system.
    """
    try:
        import qualibrate_config.vars
        original_filename = qualibrate_config.vars.DEFAULT_CONFIG_FILENAME
        new_filename = "nonexisting_config_for_testing.toml"
        qualibrate_config.vars.DEFAULT_CONFIG_FILENAME = new_filename
        yield
        qualibrate_config.vars.DEFAULT_CONFIG_FILENAME = original_filename
    except ImportError:
        # qualibrate_config not available, no need to mock
        yield


@pytest.fixture(scope="function", autouse=True)
def mock_quam_config():
    """
    Mock get_quam_config to prevent loading system config during tests.

    Patches all import locations where get_quam_config is used to ensure
    no config files are loaded from the system during testing.

    Returns a minimal mock config object with default values matching QuamConfig.
    """
    # Create a minimal mock config object that matches QuamConfig structure
    class MockSerializationConfig:
        include_defaults = True

    class MockQuamConfig:
        version = 3
        state_path = None
        raise_error_missing_reference = False
        serialization = MockSerializationConfig()

    mock_config = MockQuamConfig()

    import_locations = [
        'quam.config.resolvers.get_quam_config',  # Source - covers all imports
        'quam.core.quam_classes.get_quam_config',
        'quam.serialisation.json.get_quam_config',
        'quam.components.get_quam_config',
    ]

    patches = []
    mocks = []

    for location in import_locations:
        p = patch(location)
        mock = p.start()
        mock.return_value = mock_config
        patches.append(p)
        mocks.append(mock)

    yield mocks

    for p in patches:
        p.stop()
