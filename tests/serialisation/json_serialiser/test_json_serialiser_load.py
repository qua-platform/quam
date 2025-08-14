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


def test_load_from_directory_skip_hidden_folders(serialiser, tmp_path):
    """Test that hidden folders (starting with dot) are skipped during loading."""
    dirpath = tmp_path / "load_dir_hidden"
    dirpath.mkdir()

    # Create valid JSON files in regular directories
    regular_content = {"component1": {"id": "regular", "value": 1}}
    regular_file = dirpath / "component1.json"
    with regular_file.open("w", encoding="utf-8") as f:
        json.dump(regular_content, f)

    # Create hidden directories with JSON files that should be skipped
    hidden_dir1 = dirpath / ".ipynb_checkpoints"
    hidden_dir1.mkdir()
    checkpoint_content = {"component2": {"id": "checkpoint", "value": 2}}
    checkpoint_file = hidden_dir1 / "checkpoint.json"
    with checkpoint_file.open("w", encoding="utf-8") as f:
        json.dump(checkpoint_content, f)

    # Create another hidden directory
    hidden_dir2 = dirpath / ".git"
    hidden_dir2.mkdir()
    git_content = {"component3": {"id": "git", "value": 3}}
    git_file = hidden_dir2 / "config.json"
    with git_file.open("w", encoding="utf-8") as f:
        json.dump(git_content, f)

    # Create a nested hidden directory
    nested_hidden = dirpath / "subdir" / ".hidden"
    nested_hidden.mkdir(parents=True)
    nested_content = {"component4": {"id": "nested", "value": 4}}
    nested_file = nested_hidden / "nested.json"
    with nested_file.open("w", encoding="utf-8") as f:
        json.dump(nested_content, f)

    # Load from directory - should only include regular files
    contents, metadata = serialiser._load_from_directory(dirpath)

    # Assert only regular content is loaded (hidden directories are skipped)
    assert contents == regular_content
    assert "component2" not in contents  # From .ipynb_checkpoints
    assert "component3" not in contents  # From .git
    assert "component4" not in contents  # From nested .hidden
    assert metadata["content_mapping"]["component1"] == "component1.json"
    assert len(metadata["content_mapping"]) == 1


def test_load_from_directory_skip_nested_hidden_folders(serialiser, tmp_path):
    """Test that deeply nested hidden folders are properly skipped."""
    dirpath = tmp_path / "load_dir_nested_hidden"
    dirpath.mkdir()

    # Create valid content in regular path
    regular_content = {"main": {"id": "main", "value": 1}}
    regular_file = dirpath / "main.json"
    with regular_file.open("w", encoding="utf-8") as f:
        json.dump(regular_content, f)

    # Create deeply nested hidden structure: dir/.hidden/subdir/file.json
    deeply_hidden = dirpath / "regular_dir" / ".hidden_subdir" / "another_level"
    deeply_hidden.mkdir(parents=True)
    hidden_content = {"hidden": {"id": "hidden", "value": 999}}
    hidden_file = deeply_hidden / "hidden.json"
    with hidden_file.open("w", encoding="utf-8") as f:
        json.dump(hidden_content, f)

    # Load from directory
    contents, metadata = serialiser._load_from_directory(dirpath)

    # Assert only regular content is loaded
    assert contents == regular_content
    assert "hidden" not in contents
    assert len(metadata["content_mapping"]) == 1


def test_load_from_directory_mixed_hidden_and_regular(serialiser, tmp_path):
    """Test loading with mix of hidden and regular directories at levels."""
    dirpath = tmp_path / "load_dir_mixed"
    dirpath.mkdir()

    # Create structure with mixed hidden and regular directories
    # Root level regular file
    root_content = {"root": {"value": "root"}}
    root_file = dirpath / "root.json"
    with root_file.open("w", encoding="utf-8") as f:
        json.dump(root_content, f)

    # Regular subdirectory with file
    regular_subdir = dirpath / "components"
    regular_subdir.mkdir()
    comp_content = {"components": {"comp1": {"id": "c1"}}}
    comp_file = regular_subdir / "components.json"
    with comp_file.open("w", encoding="utf-8") as f:
        json.dump(comp_content, f)

    # Hidden directory at root level
    hidden_root = dirpath / ".cache"
    hidden_root.mkdir()
    cache_content = {"cache": {"data": "cached"}}
    cache_file = hidden_root / "cache.json"
    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(cache_content, f)

    # Regular directory with hidden subdirectory
    regular_with_hidden = dirpath / "data"
    regular_with_hidden.mkdir()
    hidden_in_regular = regular_with_hidden / ".tmp"
    hidden_in_regular.mkdir()
    tmp_content = {"tmp": {"temp": "data"}}
    tmp_file = hidden_in_regular / "tmp.json"
    with tmp_file.open("w", encoding="utf-8") as f:
        json.dump(tmp_content, f)

    # Valid file in the regular 'data' directory
    data_content = {"data": {"info": "valid"}}
    data_file = regular_with_hidden / "data.json"
    with data_file.open("w", encoding="utf-8") as f:
        json.dump(data_content, f)

    # Load from directory
    contents, metadata = serialiser._load_from_directory(dirpath)

    # Expected content should only include files from non-hidden paths
    expected_contents = {
        "root": {"value": "root"},
        "components": {"comp1": {"id": "c1"}},
        "data": {"info": "valid"},
    }

    assert contents == expected_contents
    assert "cache" not in contents  # From .cache directory
    assert "tmp" not in contents  # From .tmp directory

    # Verify content mapping
    assert metadata["content_mapping"]["root"] == "root.json"
    comp_path = "components/components.json"
    assert metadata["content_mapping"]["components"] == comp_path
    assert metadata["content_mapping"]["data"] == "data/data.json"
    assert len(metadata["content_mapping"]) == 3


def test_load_from_directory_hidden_file_in_regular_dir(serialiser, tmp_path):
    """Test that hidden files in regular directories are processed."""
    dirpath = tmp_path / "load_dir_hidden_files"
    dirpath.mkdir()

    # Create a regular JSON file
    regular_content = {"regular": {"value": 1}}
    regular_file = dirpath / "regular.json"
    with regular_file.open("w", encoding="utf-8") as f:
        json.dump(regular_content, f)

    # Create a hidden JSON file (file starting with dot, not directory)
    # Note: This should still be processed since we only skip hidden directories
    hidden_file_content = {"hidden_file": {"value": 2}}
    hidden_file = dirpath / ".hidden_file.json"
    with hidden_file.open("w", encoding="utf-8") as f:
        json.dump(hidden_file_content, f)

    # Load from directory
    contents, metadata = serialiser._load_from_directory(dirpath)

    # Both files should be loaded since we only skip hidden directories
    expected_contents = {"regular": {"value": 1}, "hidden_file": {"value": 2}}

    assert contents == expected_contents
    assert metadata["content_mapping"]["regular"] == "regular.json"
    assert metadata["content_mapping"]["hidden_file"] == ".hidden_file.json"


def test_load_from_directory_only_hidden_folders(serialiser, tmp_path):
    """Test behavior when directory contains only hidden folders with JSON."""
    dirpath = tmp_path / "load_dir_only_hidden"
    dirpath.mkdir()

    # Create only hidden directories with JSON files
    hidden_dir1 = dirpath / ".ipynb_checkpoints"
    hidden_dir1.mkdir()
    checkpoint_content = {"checkpoint": {"value": 1}}
    checkpoint_file = hidden_dir1 / "checkpoint.json"
    with checkpoint_file.open("w", encoding="utf-8") as f:
        json.dump(checkpoint_content, f)

    hidden_dir2 = dirpath / ".pytest_cache"
    hidden_dir2.mkdir()
    cache_content = {"cache": {"value": 2}}
    cache_file = hidden_dir2 / "cache.json"
    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(cache_content, f)

    # Load from directory - should find no valid files and emit warning
    with pytest.warns(UserWarning, match="No JSON files found"):
        contents, metadata = serialiser._load_from_directory(dirpath)

    # Should return empty content
    assert contents == {}
    assert metadata["content_mapping"] == {}
    assert metadata["default_filename"] is None
