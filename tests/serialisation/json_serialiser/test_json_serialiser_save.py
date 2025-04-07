import pytest
import json


def test_save_split_content_basic(serialiser, sample_quam_object, tmp_path):
    """Test splitting content into specified files."""
    folder = tmp_path / "split_basic"
    # Use the QuamRoot's to_dict method
    full_contents = sample_quam_object.to_dict(include_defaults=False)

    # Expected:
    # {'components': {'comp1': {'id': 'c1'}, 'comp2': {'id': 'c2', 'value': 5}},
    #  'wiring': {'w1': 'p1', 'w2': 'p2'},
    #  'other': 'specific_value'}

    mapping = {"wiring": "wiring.json", "components": "components.json"}

    serialiser._save_split_content(full_contents, folder, mapping)

    wiring_path = folder / "wiring.json"
    components_path = folder / "components.json"
    default_path = folder / serialiser.default_filename  # state.json

    assert wiring_path.exists()
    assert components_path.exists()
    assert default_path.exists()  # 'other' remains

    with wiring_path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {"wiring": {"w1": "p1", "w2": "p2"}}
    with components_path.open("r", encoding="utf-8") as f:
        # Check against the dict representation of the components part
        expected_components = {
            "components": {
                "comp1": {
                    "id": "c1",
                    "__class__": "conftest.MockMainComponent",
                },  # value=1 is default
                "comp2": {
                    "id": "c2",
                    "value": 5,
                    "__class__": "conftest.MockMainComponent",
                },  # value=5 is not default
            }
        }
        d = json.load(f)
        assert d == expected_components
    with default_path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {
            "other": "specific_value",
            "__class__": "conftest.MockQuamRoot",
        }  # default_val is default


def test_save_split_content_missing_keys_warning(
    serialiser, sample_quam_object, tmp_path
):
    """Test warning when specified keys are missing."""
    folder = tmp_path / "split_missing"
    full_contents = sample_quam_object.to_dict(include_defaults=False)
    mapping = {"nonexistent_key": "missing.json", "wiring": "missing.json"}

    with pytest.warns(UserWarning, match="specified in content_mapping was not found"):
        serialiser._save_split_content(full_contents, folder, mapping)

    missing_path = folder / "missing.json"
    default_path = folder / serialiser.default_filename

    assert missing_path.exists()  # Should still create file for 'wiring'
    assert default_path.exists()  # 'components' and 'other' remain

    with missing_path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {
            "wiring": {"w1": "p1", "w2": "p2"}
        }  # Only wiring is saved
    with default_path.open("r", encoding="utf-8") as f:
        loaded_default = json.load(f)
        assert "components" in loaded_default
        assert "other" in loaded_default


def test_save_split_content_no_remaining(serialiser, sample_quam_object, tmp_path):
    """Test when splitting consumes all content, no default file needed."""
    folder = tmp_path / "split_no_remaining"
    full_contents = sample_quam_object.to_dict(include_defaults=False)
    # Map all keys present when not including defaults
    mapping = {
        "components": "comps.json",
        "wiring": "wires.json",
        "other": "misc.json",
    }

    serialiser._save_split_content(full_contents, folder, mapping)

    default_path = folder / serialiser.default_filename

    assert (folder / "comps.json").exists()
    assert (folder / "wires.json").exists()
    assert (folder / "misc.json").exists()
    with (folder / "misc.json").open("r", encoding="utf-8") as f:
        assert json.load(f) == {
            "other": "specific_value",
        }
    with default_path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {
            "__class__": "conftest.MockQuamRoot",
        }


def test_save_split_content_create_folder(serialiser, sample_quam_object, tmp_path):
    """Test that the target folder is created if it doesn't exist."""
    folder = tmp_path / "new_dir_split"
    assert not folder.exists()
    full_contents = sample_quam_object.to_dict()
    mapping = {"wiring": "wiring.json"}

    serialiser._save_split_content(full_contents, folder, mapping)

    assert folder.exists()
    assert (folder / "wiring.json").exists()
    assert (folder / serialiser.default_filename).exists()


def test_save_split_content_create_subfolder(serialiser, sample_quam_object, tmp_path):
    """Test creating subdirectories specified in the mapping filename."""
    folder = tmp_path / "split_subfolder"
    full_contents = sample_quam_object.to_dict()
    subfolder_name = "sub"
    mapping = {
        "wiring": f"{subfolder_name}/wiring.json",
        "components": "components.json",
    }

    serialiser._save_split_content(full_contents, folder, mapping)

    subfolder_path = folder / subfolder_name
    wiring_path = subfolder_path / "wiring.json"
    components_path = folder / "components.json"
    default_path = folder / serialiser.default_filename

    assert subfolder_path.exists()
    assert subfolder_path.is_dir()
    assert wiring_path.exists()
    assert components_path.exists()
    assert default_path.exists()

    with wiring_path.open("r", encoding="utf-8") as f:
        assert "wiring" in json.load(f)
    with components_path.open("r", encoding="utf-8") as f:
        assert "components" in json.load(f)
    with default_path.open("r", encoding="utf-8") as f:
        # Includes 'other' and default 'default_val'
        loaded_default = json.load(f)
        assert loaded_default == {
            "other": "specific_value",
            "__class__": "conftest.MockQuamRoot",
        }


def test_save_split_content_absolute_path_warning(
    serialiser, sample_quam_object, tmp_path
):
    """Test warning when an absolute path is used in content_mapping."""
    folder = tmp_path / "split_abs_warn"
    abs_path_str = str((tmp_path / "ignored_abs_path" / "wiring.json").absolute())
    full_contents = sample_quam_object.to_dict()
    mapping = {"wiring": abs_path_str}

    with pytest.warns(
        UserWarning, match="Absolute path .* in content_mapping is ignored"
    ):
        serialiser._save_split_content(full_contents, folder, mapping)

    assert (folder / "wiring.json").exists()
    assert not (tmp_path / "ignored_abs_path").exists()

    with (folder / "wiring.json").open("r", encoding="utf-8") as f:
        assert "wiring" in json.load(f)


def test_save_split_content_empty_input_no_mapping(serialiser, tmp_path):
    """Test saving completely empty content with no mapping does not save anything."""
    folder = tmp_path / "split_empty_input"
    full_contents = {}
    mapping = {}

    serialiser._save_split_content(full_contents, folder, mapping)

    assert not folder.exists()


def test_save_single_file(serialiser, sample_quam_object, tmp_path):
    """Test saving to a single JSON file when path has .json suffix."""
    filepath = tmp_path / "single_save.json"
    serialiser.save(sample_quam_object, filepath)

    assert filepath.exists()
    with filepath.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    # Compare with dict representation (default: exclude defaults)
    expected_dict = sample_quam_object.to_dict(include_defaults=False)
    expected_dict["__class__"] = (  # Class added by default for root
        f"{sample_quam_object.__module__}.{sample_quam_object.__class__.__name__}"
    )
    assert loaded == expected_dict


def test_save_single_file_include_defaults(
    serialiser_with_defaults, sample_quam_object, tmp_path
):
    """Test saving to a single JSON file including default values."""
    filepath = tmp_path / "single_save_defaults.json"
    serialiser_with_defaults.save(sample_quam_object, filepath)

    assert filepath.exists()
    with filepath.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    # Compare with dict representation including defaults
    expected_dict = sample_quam_object.to_dict(include_defaults=True)
    expected_dict["__class__"] = (
        f"{sample_quam_object.__module__}.{sample_quam_object.__class__.__name__}"
    )
    assert loaded == expected_dict


def test_save_split_via_save_method(serialiser, sample_quam_object, tmp_path):
    """Test saving split content using the main save method (path is a folder)."""
    folder = tmp_path / "save_split_folder"
    mapping = {"wiring.json": ["wiring"]}
    serialiser.save(sample_quam_object, folder, content_mapping=mapping)

    assert folder.exists()
    assert folder.is_dir()
    assert (folder / "wiring.json").exists()
    assert (folder / serialiser.default_filename).exists()  # components and other

    with (folder / "wiring.json").open("r", encoding="utf-8") as f:
        assert "wiring" in json.load(f)
    with (folder / serialiser.default_filename).open("r", encoding="utf-8") as f:
        loaded_default = json.load(f)
        assert "components" in loaded_default
        assert "other" in loaded_default
        # __class__ should also be in the default file if not split out
        assert "__class__" in loaded_default


def test_save_with_ignore(serialiser, sample_quam_object, tmp_path):
    """Test save method with 'ignore' argument for single file."""
    filepath = tmp_path / "save_ignore.json"
    ignore_keys = ["wiring", "default_val"]
    serialiser.save(sample_quam_object, filepath, ignore=ignore_keys)

    assert filepath.exists()
    with filepath.open("r", encoding="utf-8") as f:
        loaded = json.load(f)

    expected_dict = sample_quam_object.to_dict(include_defaults=False)
    expected_dict.pop("wiring", None)
    expected_dict.pop(
        "default_val", None
    )  # Will not be present anyway if include_defaults=False
    expected_dict["__class__"] = (
        f"{sample_quam_object.__module__}.{sample_quam_object.__class__.__name__}"
    )

    assert loaded == expected_dict


def test_save_split_with_ignore(serialiser, sample_quam_object, tmp_path):
    """Test save method with 'ignore' argument for split content."""
    folder = tmp_path / "save_split_ignore"
    mapping = {"components.json": ["components"]}
    ignore_keys = ["wiring"]

    serialiser.save(
        sample_quam_object, folder, content_mapping=mapping, ignore=ignore_keys
    )

    assert folder.exists()
    assert (folder / "components.json").exists()
    assert (folder / serialiser.default_filename).exists()  # 'other' + __class__
    assert not (folder / "wiring.json").exists()  # Ignored

    with (folder / "components.json").open("r", encoding="utf-8") as f:
        assert "components" in json.load(f)
    with (folder / serialiser.default_filename).open("r", encoding="utf-8") as f:
        loaded_default = json.load(f)
        assert "other" in loaded_default
        assert "__class__" in loaded_default
        assert "wiring" not in loaded_default


def test_save_unsupported_path_suffix(serialiser, sample_quam_object, tmp_path):
    """Test ValueError for unsupported file extensions."""
    filepath = tmp_path / "unsupported.txt"
    with pytest.raises(ValueError, match="Unsupported path suffix"):
        serialiser.save(sample_quam_object, filepath)


def test_save_default_path(serialiser, sample_quam_object, monkeypatch, tmp_path):
    """Test saving to default path (mocking _get_state_path)."""
    default_save_path = tmp_path / "default_state_dir"
    monkeypatch.setattr(serialiser, "_get_state_path", lambda: default_save_path)

    # Default mapping is empty, save goes to default_filename inside folder
    serialiser.save(sample_quam_object)

    expected_file = default_save_path / serialiser.default_filename
    assert default_save_path.exists()
    assert expected_file.exists()

    with expected_file.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    expected_dict = sample_quam_object.to_dict(include_defaults=False)
    expected_dict["__class__"] = (
        f"{sample_quam_object.__module__}.{sample_quam_object.__class__.__name__}"
    )
    assert loaded == expected_dict


def test_save_nested_object(serialiser, sample_quam_object_nested, tmp_path):
    """Test saving an object with properly nested QuamComponents."""
    filepath = tmp_path / "nested_save.json"
    serialiser.save(
        sample_quam_object_nested, filepath, include_defaults=False
    )  # Exclude defaults

    assert filepath.exists()
    with filepath.open("r", encoding="utf-8") as f:
        loaded = json.load(f)

    # Check structure - exclude defaults for comparison
    expected = sample_quam_object_nested.to_dict(include_defaults=False)
    expected["__class__"] = (
        f"{sample_quam_object_nested.__module__}.{sample_quam_object_nested.__class__.__name__}"
    )
    # Manually add __class__ for nested components if needed by loader (though save doesn't add it by default unless types mismatch)
    # expected["components"]["parent"]["__class__"] = f"{sample_quam_object_nested.components['parent'].__module__}.{sample_quam_object_nested.components['parent'].__class__.__name__}"
    # expected["components"]["parent"]["child"]["__class__"] = f"{sample_quam_object_nested.components['parent'].child.__module__}.{sample_quam_object_nested.components['parent'].child.__class__.__name__}"

    assert loaded == expected
    assert "child" in loaded["components"]["parent"]
    assert loaded["components"]["parent"]["child"]["id"] == "child1"
    # Check non-default values were saved
    assert loaded["components"]["parent"]["child"]["child_value"] == 99
    assert loaded["default_val"] == 15
