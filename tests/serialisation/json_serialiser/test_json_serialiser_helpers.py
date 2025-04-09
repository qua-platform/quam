import json
from pathlib import Path
from quam.serialisation.json import JSONSerialiser, convert_int_keys


def test_convert_int_keys_valid():
    """Test converting valid integer string keys."""
    data = {"1": "apple", "2": "banana", "not_int": "cherry"}
    expected = {1: "apple", 2: "banana", "not_int": "cherry"}
    assert convert_int_keys(data) == expected


def test_convert_int_keys_nested():
    """Test converting keys in nested dictionaries."""
    data = {"outer": {"10": "ten", "inner_str": "string"}, "5": "five"}
    # Let's simulate json.load behavior
    loaded_data = json.loads(json.dumps(data), object_hook=convert_int_keys)
    expected = {"outer": {10: "ten", "inner_str": "string"}, 5: "five"}
    assert loaded_data == expected


def test_convert_int_keys_not_dict():
    """Test passing a non-dict object."""
    data = [1, 2, 3]
    assert convert_int_keys(data) == data
    data = "a string"
    assert convert_int_keys(data) == data
    data = 123
    assert convert_int_keys(data) == data


def test_convert_int_keys_empty_dict():
    """Test with an empty dictionary."""
    data = {}
    assert convert_int_keys(data) == {}


def test_save_dict_to_json_basic(serialiser, tmp_path):
    """Test saving a simple dictionary to a JSON file."""
    filepath = tmp_path / "test_basic.json"
    contents = {"a": 1, "b": "hello", "c": [1, 2, 3]}
    serialiser._save_dict_to_json(contents, filepath)

    assert filepath.exists()
    with filepath.open("r", encoding="utf-8") as f:
        loaded_contents = json.load(f)
    assert loaded_contents == contents


def test_save_dict_to_json_empty(serialiser, tmp_path):
    """Test saving an empty dictionary."""
    filepath = tmp_path / "test_empty.json"
    contents = {}
    serialiser._save_dict_to_json(contents, filepath)

    assert filepath.exists()
    with filepath.open("r", encoding="utf-8") as f:
        loaded_contents = json.load(f)
    assert loaded_contents == contents


def test_save_dict_to_json_int_keys(serialiser, tmp_path):
    """Test saving a dictionary with integer keys (JSON saves them as strings)."""
    filepath = tmp_path / "test_int_keys.json"
    contents = {1: "one", 2: "two"}
    expected_in_file = {"1": "one", "2": "two"}  # JSON standard
    serialiser._save_dict_to_json(contents, filepath)

    assert filepath.exists()
    with filepath.open("r", encoding="utf-8") as f:
        loaded_contents = json.load(f)
    assert loaded_contents == expected_in_file


def test_save_dict_to_json_ensure_ascii_false(serialiser, tmp_path):
    """Test saving with non-ASCII characters."""
    filepath = tmp_path / "test_unicode.json"
    contents = {"char": "éàçüö"}
    serialiser._save_dict_to_json(contents, filepath)

    assert filepath.exists()
    # Read raw bytes to check encoding
    raw_content = filepath.read_text(encoding="utf-8")
    # Check if the specific unicode character is present as utf-8
    assert "éàçüö" in raw_content
    # Also check loading it back normally
    with filepath.open("r", encoding="utf-8") as f:
        loaded_contents = json.load(f)
    assert loaded_contents == contents


def test_get_state_path_from_instance(tmp_path):
    """Test _get_state_path when state_path is set in __init__."""
    instance_path = tmp_path / "instance_state"
    serialiser_inst = JSONSerialiser(state_path=instance_path)
    assert serialiser_inst._get_state_path() == instance_path.resolve()


def test_get_state_path_from_env(serialiser, mock_env, tmp_path):
    """Test _get_state_path resolution from environment variable."""
    env_path = tmp_path / "env_state"
    mock_env("QUAM_STATE_PATH", env_path)
    assert serialiser._get_state_path() == env_path.resolve()


def test_get_state_path_from_config(serialiser, mock_config, tmp_path):
    """Test _get_state_path resolution from quam config."""
    config_path = tmp_path / "config_state"
    mock_config.state_path = config_path
    assert serialiser._get_state_path() == config_path.resolve()


def test_get_state_path_precedence(mock_env, mock_config, tmp_path):
    """Test the precedence order: instance > env > config."""
    instance_path = tmp_path / "instance_state"
    env_path = tmp_path / "env_state"
    config_path = tmp_path / "config_state"

    # Set all paths
    serialiser_inst = JSONSerialiser(state_path=instance_path)
    mock_env("QUAM_STATE_PATH", env_path)
    mock_config.state_path = config_path

    # 1. Instance path should take precedence
    assert serialiser_inst._get_state_path() == instance_path.resolve()

    # 2. Without instance path, env should take precedence
    serialiser_env = JSONSerialiser()  # No instance path
    assert serialiser_env._get_state_path() == env_path.resolve()

    # 3. Without instance or env path, config should be used
    mock_env("QUAM_STATE_PATH", None)  # Clear env var
    serialiser_cfg = JSONSerialiser()
    # We need to ensure mock_config is active for this part of the test
    # Re-apply or ensure the fixture scope covers this
    assert serialiser_cfg._get_state_path() == config_path.resolve()


def test_get_state_path_default(serialiser, mock_env, mock_config):
    """Test _get_state_path when no path can be found."""
    # Ensure no paths are set via mocks provided by fixtures
    assert not serialiser.content_mapping
    assert serialiser._get_state_path() == Path(serialiser.default_filename).resolve()
