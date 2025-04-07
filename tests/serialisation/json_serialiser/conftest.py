import pytest
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Union, Optional
from dataclasses import field

# Ensure quam imports work correctly relative to the project structure
# This might need adjustment based on your exact test setup location
# import sys
# sys.path.insert(0, str(Path(__file__).parent.parent)) # Assuming tests are one level above quam package

# Try to import the necessary module for the new fixture
try:
    import qualibrate_config.vars
except ImportError:
    qualibrate_config = None  # Flag that the module is missing

from quam.core import QuamRoot, QuamComponent, quam_dataclass
from quam.serialisation.json import JSONSerialiser, convert_int_keys

# Import the actual config model to get the expected version
try:
    from quam.config.models import QuamConfig

    EXPECTED_CONFIG_VERSION = QuamConfig.version
except ImportError:
    # Fallback if models can't be imported (less robust)
    EXPECTED_CONFIG_VERSION = 1


# Mock QUAM Components


@quam_dataclass
class MockChildComponent(QuamComponent):
    """A simple nested component."""

    id: Union[str, int] = "child_id"
    child_value: int = 50  # Default value


@quam_dataclass
class MockMainComponent(QuamComponent):
    """A mock component that can hold a child."""

    id: Union[str, int] = "main_id"
    value: int = 1  # Default value
    child: Optional[MockChildComponent] = None


@quam_dataclass
class MockQuamRoot(QuamRoot):
    """A mock QuamRoot for testing serialization."""

    # Use default_factory for mutable defaults like dict
    components: Dict[str, MockMainComponent] = field(default_factory=dict)
    wiring: Dict[str, Any] = field(default_factory=dict)
    other: str = "default_other"
    default_val: int = 10  # Example default


# Fixture to prevent loading user's default config
@pytest.fixture(autouse=True, scope="session")
def prevent_default_config_loading():
    """
    Overrides the default config filename during tests to prevent
    loading a user's actual config file when testing default path logic.
    """
    if qualibrate_config is None:
        print(
            "\nSkipping prevent_default_config_loading fixture: qualibrate_config.vars"
            " not found."
        )
        yield
        return

    original_filename = qualibrate_config.vars.DEFAULT_CONFIG_FILENAME
    new_filename = "nonexisting_config_for_testing.toml"
    qualibrate_config.vars.DEFAULT_CONFIG_FILENAME = new_filename
    yield  # Let the tests run with the modified filename
    qualibrate_config.vars.DEFAULT_CONFIG_FILENAME = original_filename


@pytest.fixture
def serialiser():
    """Basic JSONSerialiser instance."""
    return JSONSerialiser()


@pytest.fixture
def serialiser_with_defaults():
    """JSONSerialiser instance configured to include defaults."""
    return JSONSerialiser(include_defaults=True)


@pytest.fixture
def sample_quam_object():
    """Provides a simple mock QuamRoot object for testing."""
    root = MockQuamRoot(
        components={
            "comp1": MockMainComponent(id="c1"),  # Default value=1
            "comp2": MockMainComponent(id="c2", value=5),  # Non-default value
        },
        wiring={"w1": "p1", "w2": "p2"},
        other="specific_value",  # Non-default value
        # default_val uses its default (10)
    )
    return root


@pytest.fixture
def sample_quam_object_nested():
    """Provides a mock QuamRoot object with nested components."""
    child_comp = MockChildComponent(id="child1", child_value=99)  # Non-default
    parent_comp = MockMainComponent(id="parent1", child=child_comp)

    root = MockQuamRoot(
        components={"parent": parent_comp},
        wiring={"w1": "p1"},
        default_val=15,  # Non-default
    )
    return root


@pytest.fixture
def sample_dict_basic():
    """A simple dictionary for basic load/save tests."""
    return {"a": 1, "b": "hello", "c": [1, 2, 3]}


@pytest.fixture
def sample_dict_int_keys():
    """Represents how a dict with int keys is stored in JSON (string keys)."""
    return {"1": "one", "5": "five", "key": "value"}


@pytest.fixture
def setup_single_file(tmp_path, sample_dict_basic):
    """Creates a single JSON file for load testing."""
    filepath = tmp_path / "load_single.json"
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(sample_dict_basic, f)
    return filepath


@pytest.fixture
def setup_directory_basic(tmp_path, sample_dict_basic):
    """Creates a directory with a single default JSON file."""
    dirpath = tmp_path / "load_dir_basic"
    dirpath.mkdir()
    filepath = dirpath / JSONSerialiser.default_filename  # state.json
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(sample_dict_basic, f)
    return dirpath


@pytest.fixture
def setup_directory_split(tmp_path):
    """
    Creates a directory with split JSON files based on sample_quam_object structure.
    """
    dirpath = tmp_path / "load_dir_split"
    dirpath.mkdir()
    # Content based on sample_quam_object (excluding defaults)
    wiring_content = {"wiring": {"w1": "p1", "w2": "p2"}}
    components_content = {
        "components": {"comp1": {"id": "c1"}, "comp2": {"id": "c2", "value": 5}}
    }
    default_content = {"other": "specific_value"}

    with (dirpath / "wiring.json").open("w", encoding="utf-8") as f:
        json.dump(wiring_content, f)
    with (dirpath / "components.json").open("w", encoding="utf-8") as f:
        json.dump(components_content, f)
    with (dirpath / JSONSerialiser.default_filename).open("w", encoding="utf-8") as f:
        json.dump(default_content, f)
    # We also need the __class__ attribute for proper loading of the root
    default_content_root_class = default_content.copy()
    # Determine class path dynamically
    root_class_path = f"{MockQuamRoot.__module__}.{MockQuamRoot.__name__}"
    default_content_root_class["__class__"] = root_class_path
    with (dirpath / JSONSerialiser.default_filename).open("w", encoding="utf-8") as f:
        json.dump(default_content_root_class, f)

    # Also save __class__ for components if needed by loader (though QuamRoot.load
    # handles this)
    components_content_class = components_content.copy()
    comp_class_path = f"{MockMainComponent.__module__}.{MockMainComponent.__name__}"
    for comp_data in components_content_class["components"].values():
        comp_data["__class__"] = comp_class_path
    with (dirpath / "components.json").open("w", encoding="utf-8") as f:
        json.dump(components_content_class, f)

    return dirpath


@pytest.fixture
def setup_directory_conflict(tmp_path):
    """Creates a directory with files having conflicting keys."""
    dirpath = tmp_path / "load_dir_conflict"
    dirpath.mkdir()
    file1_content = {"a": 1, "b": "original"}
    file2_content = {"b": "overwrite", "c": 3}  # 'b' conflicts

    with (dirpath / "file1.json").open("w", encoding="utf-8") as f:
        json.dump(file1_content, f)
    with (dirpath / "file2.json").open("w", encoding="utf-8") as f:
        json.dump(file2_content, f)
    return dirpath


@pytest.fixture
def setup_directory_int_keys(tmp_path, sample_dict_int_keys):
    """Creates a directory with integer keys saved as strings."""
    dirpath = tmp_path / "load_dir_int_keys"
    dirpath.mkdir()
    filepath = dirpath / "int_keys.json"
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(sample_dict_int_keys, f)
    return dirpath


# Mocking fixtures
@pytest.fixture
def mock_env(monkeypatch):
    """Fixture to mock environment variables."""
    original_env = os.environ.copy()

    def set_env(var, value):
        if value is None:
            monkeypatch.delenv(var, raising=False)
        else:
            monkeypatch.setenv(var, str(value))

    yield set_env
    # Restore original environment state after test
    os.environ.clear()
    os.environ.update(original_env)


# UPDATED mock_config fixture
@pytest.fixture
def mock_config(monkeypatch):
    """Fixture to mock quam.config get_quam_config function."""

    class MockConfigContainer:
        """Helper class to hold the state for the mock config."""

        state_path: Optional[Path] = None
        raise_exception: bool = False
        config_found: bool = True

    mock_config_data = MockConfigContainer()

    def mock_get_config_replacement():
        """Replacement for quam.config.get_quam_config"""
        if not mock_config_data.config_found:
            return None  # Simulate config not found
        if mock_config_data.raise_exception:
            raise RuntimeError("Simulated config loading error")

        # Create a basic object that mimics the necessary structure
        # needed by _get_state_path and its internal calls.
        class MockQuamConfigData:
            # Provide the version attribute expected by validators
            version = EXPECTED_CONFIG_VERSION
            state_path = None  # Initialize state_path

        mock_cfg = MockQuamConfigData()
        mock_cfg.state_path = mock_config_data.state_path  # Set state_path if provided

        return mock_cfg  # Return the object

    # Attempt to mock, handling potential ImportError
    try:
        import quam.config  # noqa: F401

        # Mock the get_quam_config function where it's used
        monkeypatch.setattr(
            "quam.serialisation.json.get_quam_config",
            mock_get_config_replacement,
            raising=False,
        )
    except ImportError:
        # Simulate the ImportError scenario for _get_state_path
        monkeypatch.setattr(
            "quam.serialisation.json.get_quam_config", None, raising=False
        )
        # Also handle the direct import within _get_state_path if it fails
        monkeypatch.setitem(sys.modules, "quam.config", None)

    yield mock_config_data  # Tests can modify mock_config_data.state_path etc.

    # Cleanup
    monkeypatch.undo()
    if "quam.config" in sys.modules and sys.modules["quam.config"] is None:
        del sys.modules["quam.config"]
