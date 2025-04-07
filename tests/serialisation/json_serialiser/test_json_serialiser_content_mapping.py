import json
import pytest
from quam.serialisation.json import JSONSerialiser


def test_save_backwards_compatibility_single_dict(
    serialiser, sample_quam_object, tmp_path
):
    """Test save still works with a single dict mapping (backward compatibility)."""
    target_folder = tmp_path / "single_dict_save"
    single_mapping = {"wiring_bc.json": ["wiring"]}

    serialiser.save(
        quam_obj=sample_quam_object,
        path=target_folder,
        content_mapping=single_mapping,
        include_defaults=False,
    )

    wiring_path = target_folder / "wiring_bc.json"
    default_path = target_folder / serialiser.default_filename

    assert wiring_path.exists()
    assert default_path.exists()
    with wiring_path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {"wiring": sample_quam_object.wiring}
    with default_path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
        assert "components" in loaded
        assert loaded["other"] == "specific_value"
        assert loaded["__class__"] == "conftest.MockQuamRoot"


def test_validate_and_convert_content_mapping_new_format():
    """Test new format content mapping is correctly identified and validated."""
    # New format: component -> filename
    new_format = {"component1": "file1.json", "component2": "file2.json"}
    result = JSONSerialiser._validate_and_convert_content_mapping(new_format)
    assert result == new_format

    # String to string mapping should be identified as new format
    string_to_string = {"hi": "bye.json"}
    result = JSONSerialiser._validate_and_convert_content_mapping(string_to_string)
    assert result == string_to_string


def test_validate_and_convert_content_mapping_old_format():
    """Test old format content mapping is correctly identified and converted."""
    # Old format: filename -> [components]
    old_format_list = {"file.json": ["component1", "component2"]}
    expected = {"component1": "file.json", "component2": "file.json"}
    result = JSONSerialiser._validate_and_convert_content_mapping(old_format_list)
    assert result == expected

    # Test with tuple
    old_format_tuple = {"file.json": ("component1", "component2")}
    result = JSONSerialiser._validate_and_convert_content_mapping(old_format_tuple)
    assert result == expected

    # Test with set
    old_format_set = {"file.json": {"component1", "component2"}}
    result = JSONSerialiser._validate_and_convert_content_mapping(old_format_set)
    # Sets are unordered, so just check keys
    assert set(result.keys()) == {"component1", "component2"}
    assert all(value == "file.json" for value in result.values())


def test_validate_and_convert_content_mapping_conflicts():
    """Test handling of conflicts in old format conversion."""
    # Components assigned to multiple files
    conflicting_mapping = {
        "file1.json": ["component1", "component2"],
        "file2.json": ["component2", "component3"],  # component2 appears twice
    }
    result = JSONSerialiser._validate_and_convert_content_mapping(conflicting_mapping)
    # component2 should get the last assignment (file2.json)
    assert result["component1"] == "file1.json"
    assert result["component2"] == "file2.json"
    assert result["component3"] == "file2.json"


def test_validate_and_convert_content_mapping_invalid():
    """Test invalid content mapping formats."""
    # Mixed value types
    with pytest.raises(TypeError):
        JSONSerialiser._validate_and_convert_content_mapping(
            {"file1.json": ["component1"], "component2": "file2.json"}
        )

    # Invalid key in old format
    with pytest.raises(TypeError):
        JSONSerialiser._validate_and_convert_content_mapping({123: ["component1"]})

    # Invalid value in old format
    with pytest.raises(TypeError):
        JSONSerialiser._validate_and_convert_content_mapping({"file.json": [123]})

    # Invalid key in new format
    with pytest.raises(TypeError):
        JSONSerialiser._validate_and_convert_content_mapping({123: "file.json"})

    # Invalid value in new format
    with pytest.raises(TypeError):
        JSONSerialiser._validate_and_convert_content_mapping({"component": 123})


def test_validate_and_convert_content_mapping_empty():
    """Test handling of empty content mapping."""
    assert JSONSerialiser._validate_and_convert_content_mapping({}) == {}
    assert JSONSerialiser._validate_and_convert_content_mapping(None) == {}
