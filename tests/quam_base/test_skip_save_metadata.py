"""Tests for skip_save field metadata functionality.

This module tests the ability to exclude specific dataclass fields from
serialization using field(metadata={'skip_save': True}).
"""
from dataclasses import field
from typing import ClassVar
import tempfile
import json
from quam.core import QuamRoot, QuamComponent, QuamDict, QuamList, quam_dataclass


# Basic functionality tests
def test_skip_save_basic():
    """Test that fields with skip_save=True are excluded from to_dict()."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = 1
        hidden: int = field(default=2, metadata={"skip_save": True})

    obj = TestComponent()
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result
    assert "hidden" not in result
    assert "__class__" in result
    assert result["visible"] == 1


def test_skip_save_false_explicit():
    """Test that fields with skip_save=False are included."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = 1
        also_visible: int = field(default=2, metadata={"skip_save": False})

    obj = TestComponent()
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result
    assert "also_visible" in result
    assert result["also_visible"] == 2


def test_skip_save_no_metadata():
    """Test that fields without metadata are included by default."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        field_a: int = 1
        field_b: int = 2

    obj = TestComponent()
    result = obj.to_dict(include_defaults=True)

    assert "field_a" in result
    assert "field_b" in result


def test_skip_save_multiple_fields():
    """Test multiple fields with mixed skip_save values."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible_1: int = 1
        hidden_1: int = field(default=2, metadata={"skip_save": True})
        visible_2: str = "test"
        hidden_2: float = field(default=3.14, metadata={"skip_save": True})

    obj = TestComponent()
    result = obj.to_dict(include_defaults=True)

    assert "visible_1" in result
    assert "visible_2" in result
    assert "hidden_1" not in result
    assert "hidden_2" not in result


def test_skip_save_runtime_accessible():
    """Test that skipped fields remain accessible at runtime."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = 1
        hidden: int = field(default=2, metadata={"skip_save": True})

    obj = TestComponent()

    # Runtime access should work
    assert obj.visible == 1
    assert obj.hidden == 2

    # Modification should work
    obj.hidden = 99
    assert obj.hidden == 99

    # But still excluded from serialization
    result = obj.to_dict()
    assert "hidden" not in result


# Nested component tests
def test_skip_save_nested_component():
    """Test that skipped field with QuamComponent excludes entire subtree."""
    @quam_dataclass
    class InnerComponent(QuamComponent):
        inner_val: int = 1

    @quam_dataclass
    class OuterComponent(QuamComponent):
        visible: int = 2
        hidden: InnerComponent = field(
            default_factory=InnerComponent, metadata={"skip_save": True}
        )

    obj = OuterComponent()
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result
    assert "hidden" not in result
    # Inner component's inner_val should not appear anywhere
    assert "inner_val" not in str(result)


def test_skip_save_deeply_nested():
    """Test skip_save with deeply nested component tree."""
    @quam_dataclass
    class Level3(QuamComponent):
        val3: int = 3

    @quam_dataclass
    class Level2(QuamComponent):
        val2: int = 2
        level3: Level3 = field(default_factory=Level3)

    @quam_dataclass
    class Level1(QuamComponent):
        val1: int = 1
        level2: Level2 = field(default_factory=Level2, metadata={"skip_save": True})

    obj = Level1()
    result = obj.to_dict(include_defaults=True)

    assert "val1" in result
    assert "level2" not in result
    # Entire subtree should be excluded
    assert "val2" not in str(result)
    assert "val3" not in str(result)


def test_skip_save_with_quam_dict_in_field():
    """Test skip_save on field containing QuamDict."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = 1
        hidden_dict: QuamDict = field(
            default_factory=QuamDict, metadata={"skip_save": True}
        )

    obj = TestComponent()
    obj.hidden_dict["key"] = "value"
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result
    assert "hidden_dict" not in result


def test_skip_save_with_quam_list_in_field():
    """Test skip_save on field containing QuamList."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = 1
        hidden_list: QuamList = field(
            default_factory=QuamList, metadata={"skip_save": True}
        )

    obj = TestComponent()
    obj.hidden_list.append("item")
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result
    assert "hidden_list" not in result


# Inheritance tests
def test_skip_save_inherited_field():
    """Test that inherited field with skip_save metadata is respected."""
    @quam_dataclass
    class ParentComponent(QuamComponent):
        inherited_visible: int = 1
        inherited_hidden: int = field(default=2, metadata={"skip_save": True})

    @quam_dataclass
    class ChildComponent(ParentComponent):
        child_field: int = 3

    obj = ChildComponent()
    result = obj.to_dict(include_defaults=True)

    assert "inherited_visible" in result
    assert "child_field" in result
    assert "inherited_hidden" not in result


def test_skip_save_field_override_removes_metadata():
    """Test that overriding a field in child class can remove skip_save."""
    @quam_dataclass
    class ParentComponent(QuamComponent):
        field: int = field(default=1, metadata={"skip_save": True})

    @quam_dataclass
    class ChildComponent(ParentComponent):
        field: int = 2  # Override without metadata

    obj = ChildComponent()
    result = obj.to_dict(include_defaults=True)

    # Field should now be visible since metadata was removed
    assert "field" in result
    assert result["field"] == 2


def test_skip_save_multiple_inheritance_levels():
    """Test skip_save behavior across multiple inheritance levels."""
    @quam_dataclass
    class GrandParent(QuamComponent):
        gp_visible: int = 1
        gp_hidden: int = field(default=2, metadata={"skip_save": True})

    @quam_dataclass
    class Parent(GrandParent):
        p_visible: int = 3
        p_hidden: int = field(default=4, metadata={"skip_save": True})

    @quam_dataclass
    class Child(Parent):
        c_visible: int = 5

    obj = Child()
    result = obj.to_dict(include_defaults=True)

    assert "gp_visible" in result
    assert "p_visible" in result
    assert "c_visible" in result
    assert "gp_hidden" not in result
    assert "p_hidden" not in result


# Integration tests
def test_skip_save_with_get_attrs():
    """Test that get_attrs() respects skip_save metadata."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = 1
        hidden: int = field(default=2, metadata={"skip_save": True})

    obj = TestComponent()
    attrs = obj.get_attrs()

    assert "visible" in attrs
    assert "hidden" not in attrs


def test_skip_save_save_load_roundtrip():
    """Test that skipped fields are excluded from saved JSON."""
    @quam_dataclass
    class TestRoot(QuamRoot):
        visible: int = 1
        hidden: int = field(default=2, metadata={"skip_save": True})

    obj = TestRoot()
    obj.hidden = 99  # Set to non-default value

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        # Save to file
        obj.save(temp_path)

        # Load and inspect raw JSON
        with open(temp_path, "r") as f:
            saved_data = json.load(f)

        assert "visible" in saved_data
        assert "hidden" not in saved_data

        # Load from file
        loaded = TestRoot.load(temp_path)
        assert loaded.visible == 1
        # Hidden field should have default value since it wasn't saved
        assert loaded.hidden == 2

    finally:
        import os
        os.unlink(temp_path)


def test_skip_save_with_skip_attrs():
    """Test that skip_save works alongside _skip_attrs mechanism."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        _skip_attrs = ["programmatic_skip"]

        visible: int = 1
        programmatic_skip: int = 2
        metadata_skip: int = field(default=3, metadata={"skip_save": True})

    obj = TestComponent()
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result
    assert "programmatic_skip" not in result
    assert "metadata_skip" not in result


def test_skip_save_with_include_defaults_false():
    """Test skip_save interaction with include_defaults parameter."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible_default: int = 1
        visible_nondefault: int = 2
        hidden_default: int = field(default=3, metadata={"skip_save": True})

    obj = TestComponent()
    obj.visible_nondefault = 99

    # With defaults
    result_with_defaults = obj.to_dict(include_defaults=True)
    assert "visible_default" in result_with_defaults
    assert "visible_nondefault" in result_with_defaults
    assert "hidden_default" not in result_with_defaults

    # Without defaults
    result_no_defaults = obj.to_dict(include_defaults=False)
    assert "visible_default" not in result_no_defaults
    assert "visible_nondefault" in result_no_defaults
    assert "hidden_default" not in result_no_defaults


def test_skip_save_with_multiple_metadata_entries():
    """Test that skip_save works alongside other metadata."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = 1
        hidden: int = field(
            default=2, metadata={"skip_save": True, "custom_key": "custom_value"}
        )

    obj = TestComponent()
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result
    assert "hidden" not in result


def test_skip_save_nondefault_value():
    """Test that skip_save takes precedence over value being non-default."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        hidden: int = field(default=1, metadata={"skip_save": True})

    obj = TestComponent(hidden=99)  # Set to non-default value
    result = obj.to_dict()

    # Should still be skipped even with non-default value
    assert "hidden" not in result


# Edge case tests
def test_skip_save_empty_metadata():
    """Test that empty metadata dict doesn't cause issues."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = field(default=1, metadata={})

    obj = TestComponent()
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result


def test_skip_save_classvar_not_affected():
    """Test that ClassVar fields are not affected by skip_save logic."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        class_var: ClassVar[int] = 99
        visible: int = 1
        hidden: int = field(default=2, metadata={"skip_save": True})

    obj = TestComponent()
    result = obj.to_dict(include_defaults=True)

    # ClassVar should not appear regardless
    assert "class_var" not in result
    assert "visible" in result
    assert "hidden" not in result


def test_skip_save_with_required_field():
    """Test skip_save on a required field (no default)."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int
        hidden: int = field(metadata={"skip_save": True})

    obj = TestComponent(visible=1, hidden=2)
    result = obj.to_dict()

    assert "visible" in result
    assert "hidden" not in result


def test_skip_save_field_with_default_factory():
    """Test skip_save with default_factory fields."""
    @quam_dataclass
    class TestComponent(QuamComponent):
        visible: int = 1
        hidden: list = field(default_factory=list, metadata={"skip_save": True})

    obj = TestComponent()
    obj.hidden.append("item")
    result = obj.to_dict(include_defaults=True)

    assert "visible" in result
    assert "hidden" not in result
