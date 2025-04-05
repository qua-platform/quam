import pytest
import json

# Mock components and fixtures are now imported from conftest.py
# Import the mock classes to check against after loading
from conftest import MockQuamRoot, MockMainComponent
from quam.serialisation.json import JSONSerialiser


def test_load_from_file_basic(serialiser, setup_single_file, sample_dict_basic):
    """Test loading from a basic single JSON file."""
    contents, metadata = serialiser._load_from_file(setup_single_file)
    assert contents == sample_dict_basic
    assert metadata["default_filename"] == setup_single_file.name
    assert metadata["content_mapping"] == {}
    assert metadata["default_foldername"] is None


def test_load_from_file_int_keys(serialiser, tmp_path, sample_dict_int_keys):
    """Test loading file with string keys that should be converted to int."""
    filepath = tmp_path / "load_int_keys.json"
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(sample_dict_int_keys, f)  # Save with string keys

    contents, _ = serialiser._load_from_file(filepath)

    expected_contents = {1: "one", 5: "five", "key": "value"}  # Keys converted
    assert contents == expected_contents


def test_load_from_file_not_json(serialiser, tmp_path):
    """Test loading a file that is not JSON."""
    filepath = tmp_path / "not_json.txt"
    filepath.write_text("This is not JSON")
    with pytest.raises(TypeError, match="not a JSON file"):
        serialiser._load_from_file(filepath)


def test_load_from_file_invalid_json(serialiser, tmp_path):
    """Test loading a file with invalid JSON content."""
    filepath = tmp_path / "invalid.json"
    filepath.write_text("{a: 1, b: 2")  # Missing closing brace
    with pytest.raises(json.JSONDecodeError):
        serialiser._load_from_file(filepath)


def test_load_from_file_io_error(serialiser, tmp_path):
    """Test loading a file that causes an IOError (e.g., permissions)."""
    filepath = tmp_path / "no_read.json"
    # Create file but make it unreadable
    try:
        filepath.touch()
        filepath.chmod(0o000)  # Remove read permissions
        with pytest.raises(IOError):
            serialiser._load_from_file(filepath)
    finally:
        # Ensure permissions are restored for cleanup, even if test fails
        filepath.chmod(0o644)


def test_load_from_directory_basic(
    serialiser, setup_directory_basic, sample_dict_basic
):
    """Test loading from a directory with only the default file."""
    contents, metadata = serialiser._load_from_directory(setup_directory_basic)
    assert contents == sample_dict_basic
    assert metadata["default_filename"] == JSONSerialiser.default_filename
    assert metadata["content_mapping"] == {}  # No split files found
    assert metadata["default_foldername"] == str(setup_directory_basic)


def test_load_from_directory_split(serialiser, setup_directory_split):
    """Test loading and merging from a directory with split files."""
    contents, metadata = serialiser._load_from_directory(setup_directory_split)

    # Construct expected dict based on files created in setup_directory_split
    expected_contents = {
        "wiring": {"w1": "p1", "w2": "p2"},
        "components": {
            "comp1": {"id": "c1", "__class__": "conftest.MockMainComponent"},
            "comp2": {
                "id": "c2",
                "value": 5,
                "__class__": "conftest.MockMainComponent",
            },
        },
        "other": "specific_value",
        "__class__": "conftest.MockQuamRoot",
    }
    assert contents == expected_contents

    assert metadata["default_filename"] == JSONSerialiser.default_filename
    assert metadata["default_foldername"] == str(setup_directory_split)
    assert metadata["content_mapping"]["wiring"] == "wiring.json"
    assert metadata["content_mapping"]["components"] == "components.json"


def test_load_from_directory_conflict_warning(serialiser, setup_directory_conflict):
    """Test warning when loading files with conflicting keys."""
    with pytest.warns(UserWarning, match="Key conflicts detected"):
        contents, _ = serialiser._load_from_directory(setup_directory_conflict)

    assert contents == {"a": 1, "b": "overwrite", "c": 3} or contents == {
        "a": 1,
        "b": "original",
        "c": 3,
    }


def test_load_from_directory_empty(serialiser, tmp_path):
    """Test loading from an empty directory."""
    dirpath = tmp_path / "load_dir_empty"
    dirpath.mkdir()

    with pytest.warns(UserWarning, match="No JSON files found"):
        contents, metadata = serialiser._load_from_directory(dirpath)

    assert contents == {}
    assert metadata["default_filename"] is None
    assert metadata["content_mapping"] == {}
    assert metadata["default_foldername"] == str(dirpath)


def test_load_from_directory_skip_invalid_file(serialiser, tmp_path):
    """Test skipping invalid JSON files in a directory."""
    dirpath = tmp_path / "load_dir_invalid"
    dirpath.mkdir()
    valid_content = {"a": 1}
    invalid_content = "{invalid json"

    (dirpath / "valid.json").write_text(json.dumps(valid_content), encoding="utf-8")
    (dirpath / "invalid.json").write_text(invalid_content, encoding="utf-8")

    with pytest.warns(UserWarning, match="Skipping file .*invalid.json"):
        contents, _ = serialiser._load_from_directory(dirpath)

    assert contents == valid_content  # Only valid content should be loaded


def test_load_from_directory_int_keys(serialiser, setup_directory_int_keys):
    """Test loading from directory converts int keys correctly."""
    contents, _ = serialiser._load_from_directory(setup_directory_int_keys)
    expected_contents = {1: "one", 5: "five", "key": "value"}  # Keys converted
    assert contents == expected_contents


def test_load_single_file_path(serialiser, setup_single_file, sample_dict_basic):
    """Test load method with a path to a single file."""
    contents, metadata = serialiser.load(setup_single_file)
    assert contents == sample_dict_basic
    assert metadata["default_filename"] == setup_single_file.name


def test_load_directory_path(serialiser, setup_directory_split):
    """Test load method with a path to a directory."""
    contents, metadata = serialiser.load(setup_directory_split)

    # Expected merged content after loading from split directory
    expected_contents = {
        "wiring": {"w1": "p1", "w2": "p2"},
        "components": {
            "comp1": {"id": "c1", "__class__": "conftest.MockMainComponent"},
            "comp2": {
                "id": "c2",
                "value": 5,
                "__class__": "conftest.MockMainComponent",
            },
        },
        "other": "specific_value",
        "__class__": "conftest.MockQuamRoot",
    }
    assert contents == expected_contents
    assert metadata["default_foldername"] == str(setup_directory_split)

    # Test actual QuamRoot loading (instantiation)
    # The serialiser.load only returns the dict, use QuamRoot.load for instantiation
    loaded_quam = MockQuamRoot.load(setup_directory_split)
    assert isinstance(loaded_quam, MockQuamRoot)
    assert loaded_quam.other == "specific_value"
    assert loaded_quam.wiring == {"w1": "p1", "w2": "p2"}
    assert "comp1" in loaded_quam.components
    assert isinstance(loaded_quam.components["comp1"], MockMainComponent)
    assert loaded_quam.components["comp1"].id == "c1"
    assert loaded_quam.components["comp1"].value == 1  # Default
    assert isinstance(loaded_quam.components["comp2"], MockMainComponent)
    assert loaded_quam.components["comp2"].id == "c2"
    assert loaded_quam.components["comp2"].value == 5  # Non-default


def test_load_file_not_found(serialiser, tmp_path):
    """Test load method when the path does not exist."""
    non_existent_path = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        serialiser.load(non_existent_path)


def test_load_default_path(serialiser, monkeypatch, tmp_path, sample_dict_basic):
    """Test loading from the default path (mocking _get_state_path)."""
    default_load_path = tmp_path / "default_state_dir"
    default_load_path.mkdir()
    filepath = default_load_path / serialiser.default_filename
    # Add __class__ for root loading test
    root_content = sample_dict_basic.copy()
    root_content["__class__"] = "conftest.MockQuamRoot"
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(root_content, f)

    # Mock the internal method to return our desired default path
    monkeypatch.setattr(serialiser, "_get_state_path", lambda: default_load_path)

    # 1. Test serialiser.load returns the dictionary content
    contents, metadata = serialiser.load()  # No path argument
    assert contents == root_content
    assert metadata["default_foldername"] == str(default_load_path)
