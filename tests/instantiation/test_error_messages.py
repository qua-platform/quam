"""Tests for informative error messages during QUAM state loading.

Covers three failure modes:
  1. Unexpected attribute in JSON (class definition missing it or typo in key)
  2. Missing required attribute in JSON (new field added to class, or typo in key)
  3. Source file path included in errors raised from QuamRoot.load()
"""
import json
import pytest

from quam.core import QuamRoot, QuamComponent, quam_dataclass
from quam.core.quam_instantiation import instantiate_quam_class


# ---------------------------------------------------------------------------
# Unexpected attribute errors
# ---------------------------------------------------------------------------


def test_unexpected_attr_names_the_bad_key():
    @quam_dataclass
    class TestComp(QuamComponent):
        value: int

    with pytest.raises(AttributeError, match="'unknown_attr'"):
        instantiate_quam_class(TestComp, {"value": 1, "unknown_attr": 2})


def test_unexpected_attr_lists_required_attributes():
    @quam_dataclass
    class TestComp(QuamComponent):
        required_val: int

    with pytest.raises(AttributeError, match="required_val"):
        instantiate_quam_class(TestComp, {"required_val": 1, "bad": 2})


def test_unexpected_attr_lists_optional_attributes():
    @quam_dataclass
    class TestComp(QuamComponent):
        required_val: int
        optional_val: str = "default"

    with pytest.raises(AttributeError, match="optional_val"):
        instantiate_quam_class(TestComp, {"required_val": 1, "bad": 2})


def test_unexpected_attr_suggests_close_match():
    @quam_dataclass
    class TestComp(QuamComponent):
        frequency: float

    with pytest.raises(AttributeError, match="Did you mean: 'frequency'"):
        instantiate_quam_class(TestComp, {"frequecny": 5e9})


def test_unexpected_attr_no_suggestion_for_unrelated_name():
    @quam_dataclass
    class TestComp(QuamComponent):
        value: int

    with pytest.raises(AttributeError) as exc_info:
        instantiate_quam_class(TestComp, {"value": 1, "xyz_completely_different": 2})
    assert "Did you mean" not in str(exc_info.value)


def test_unexpected_attr_includes_class_qualname():
    @quam_dataclass
    class MySpecialComp(QuamComponent):
        value: int

    with pytest.raises(AttributeError) as exc_info:
        instantiate_quam_class(MySpecialComp, {"value": 1, "bad": 2})
    assert "MySpecialComp" in str(exc_info.value)


def test_unexpected_attr_fix_attrs_false_allows_extra():
    """fix_attrs=False must not raise for unknown attributes."""

    @quam_dataclass
    class TestComp(QuamComponent):
        value: int

    obj = instantiate_quam_class(TestComp, {"value": 1, "extra": 99}, fix_attrs=False)
    assert obj.extra == 99


# ---------------------------------------------------------------------------
# Missing required attribute errors
# ---------------------------------------------------------------------------


def test_missing_required_names_the_missing_attribute():
    @quam_dataclass
    class TestComp(QuamComponent):
        required_val: int

    with pytest.raises(AttributeError, match="'required_val'"):
        instantiate_quam_class(TestComp, {})


def test_missing_required_shows_expected_type():
    @quam_dataclass
    class TestComp(QuamComponent):
        required_val: int

    with pytest.raises(AttributeError, match="int"):
        instantiate_quam_class(TestComp, {})


def test_missing_required_shows_provided_keys():
    @quam_dataclass
    class TestComp(QuamComponent):
        required_val: int
        optional_val: str = "default"

    # "optional_val" is provided but "required_val" is absent
    with pytest.raises(AttributeError, match="optional_val"):
        instantiate_quam_class(TestComp, {"optional_val": "hi"})


def test_missing_required_suggests_typo_in_provided_keys():
    @quam_dataclass
    class TestComp(QuamComponent):
        frequency: float

    # The key is a typo of the required attribute name
    with pytest.raises(AttributeError, match="frequecny"):
        instantiate_quam_class(TestComp, {"frequecny": 5e9})


def test_missing_required_includes_class_qualname():
    @quam_dataclass
    class MySpecialComp(QuamComponent):
        required_val: int

    with pytest.raises(AttributeError) as exc_info:
        instantiate_quam_class(MySpecialComp, {})
    assert "MySpecialComp" in str(exc_info.value)


def test_missing_required_all_missing_attrs_listed():
    @quam_dataclass
    class TestComp(QuamComponent):
        first_val: int
        second_val: str

    with pytest.raises(AttributeError) as exc_info:
        instantiate_quam_class(TestComp, {})
    msg = str(exc_info.value)
    assert "'first_val'" in msg
    assert "'second_val'" in msg


# ---------------------------------------------------------------------------
# QuamRoot.load() file-path context
# ---------------------------------------------------------------------------


def test_load_from_file_attribute_error_includes_path(tmp_path):
    class TestRoot(QuamRoot):
        required_val: int

    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"unknown_key": 42}))

    with pytest.raises(AttributeError) as exc_info:
        TestRoot.load(state_file)
    assert str(state_file) in str(exc_info.value)


def test_load_from_file_type_error_includes_path(tmp_path):
    class TestRoot(QuamRoot):
        int_val: int

    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"int_val": "not_an_int"}))

    with pytest.raises(TypeError) as exc_info:
        TestRoot.load(state_file)
    assert str(state_file) in str(exc_info.value)


def test_load_from_dict_does_not_add_file_path_to_error():
    class TestRoot(QuamRoot):
        required_val: int

    with pytest.raises(AttributeError) as exc_info:
        TestRoot.load({"unknown_key": 42})
    assert "Failed to load QUAM state from" not in str(exc_info.value)
