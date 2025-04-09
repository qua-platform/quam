import pytest
from quam.core.quam_classes import QuamBase, QuamRoot, quam_dataclass
from typing import Optional


@quam_dataclass
class ChildQuam(QuamBase):
    value: int = 0


@quam_dataclass
class ParentQuam(QuamBase):
    child: ChildQuam = None
    ref_value: str = "#./child/value"
    normal_value: int = 42


@quam_dataclass
class RootQuam(QuamRoot):
    parent: ParentQuam = None
    abs_ref: str = "#/parent/child/value"


def test_set_at_reference():
    """Test setting a value through a reference"""
    parent = ParentQuam(child=ChildQuam())

    # Set value through reference
    parent.set_at_reference("ref_value", 123)

    # Check that the value was set correctly
    assert parent.child.value == 123
    # Reference string should remain unchanged
    assert parent.get_raw_value("ref_value") == "#./child/value"


def test_set_at_reference_non_reference():
    """Test that setting a non-reference attribute raises ValueError"""
    parent = ParentQuam(child=ChildQuam())

    with pytest.raises(ValueError, match="is not a reference"):
        parent.set_at_reference("normal_value", 123)


def test_set_at_reference_invalid_reference():
    """Test handling of invalid references"""
    parent = ParentQuam(child=ChildQuam())
    parent.ref_value = "#./nonexistent/value"

    with pytest.raises(AttributeError):
        parent.set_at_reference("ref_value", 123)


def test_unreferenced_value():
    root = RootQuam(parent=ParentQuam(child=ChildQuam()))
    assert root.get_raw_value("abs_ref") == "#/parent/child/value"
    assert root.parent.get_raw_value("ref_value") == "#./child/value"


def test_set_at_absolute_reference():
    """Test setting a value through an absolute reference"""
    root = RootQuam(parent=ParentQuam(child=ChildQuam()))

    # Set value through absolute reference
    root.set_at_reference("abs_ref", 456)

    # Check that the value was set correctly
    assert root.parent.child.value == 456
    # Reference string should remain unchanged
    assert root.get_raw_value("abs_ref") == "#/parent/child/value"


def test_set_at_absolute_reference_invalid():
    """Test handling of invalid absolute references"""
    root = RootQuam(parent=ParentQuam(child=ChildQuam()))
    root.abs_ref = "#/nonexistent/path"

    with pytest.raises(AttributeError):
        root.set_at_reference("abs_ref", 456)


@quam_dataclass
class DoubleChildQuam(ChildQuam):
    value: int = 0
    child: Optional[ChildQuam] = None


def test_set_double_reference():
    """Test setting a value through a double reference"""
    double_child = DoubleChildQuam(child=ChildQuam(value=42), value="#./child/value")
    parent = ParentQuam(child=double_child, ref_value="#./child/value")

    assert parent.ref_value == 42
    assert parent.get_raw_value("ref_value") == "#./child/value"
    assert parent.child.get_raw_value("value") == "#./child/value"

    # Set value through double reference
    parent.set_at_reference("ref_value", 789)

    # Check that the value was set correctly in the nested child
    assert double_child.child.value == 789
    assert double_child.value == 789
    assert parent.ref_value == 789

    # Reference string should remain unchanged
    assert parent.get_raw_value("ref_value") == "#./child/value"
    assert double_child.get_raw_value("value") == "#./child/value"


def test_set_nonexistent_double_reference():
    """Test setting a value where the double reference does not exist"""
    double_child = DoubleChildQuam(
        child=ChildQuam(value=42), value="#./child/nonexistent"
    )
    parent = ParentQuam(child=double_child, ref_value="#./child/nonexistent")

    with pytest.raises(AttributeError):
        parent.set_at_reference("ref_value", 789)


def test_set_double_reference_to_nonexistent_item():
    """Test setting a value through a double reference to a nonexistent item"""
    double_child = DoubleChildQuam(
        child=ChildQuam(value=42), value="#./nonexistent/value"
    )
    parent = ParentQuam(child=double_child, ref_value="#./nonexistent/value")

    with pytest.raises(AttributeError):
        parent.set_at_reference("ref_value", 789)


def test_set_double_reference_with_invalid_reference():
    """Test setting a value through a double reference with an invalid reference"""
    double_child = DoubleChildQuam(child=ChildQuam(value=42), value="#./child/invalid")
    parent = ParentQuam(child=double_child, ref_value="#./child/invalid")

    with pytest.raises(AttributeError):
        parent.set_at_reference("ref_value", 789)


def test_set_triple_reference():
    """Test setting a value through a triple reference"""
    triple_child = DoubleChildQuam(
        child=DoubleChildQuam(child=ChildQuam(value=42), value="#./child/value"),
        value="#./child/value",
    )
    parent = ParentQuam(child=triple_child, ref_value="#./child/value")

    assert parent.ref_value == 42
    assert parent.get_raw_value("ref_value") == "#./child/value"
    assert parent.child.get_raw_value("value") == "#./child/value"
    assert parent.child.child.get_raw_value("value") == "#./child/value"

    # Set value through triple reference
    parent.set_at_reference("ref_value", 789)

    # Check that the value was set correctly in the nested child
    assert triple_child.child.child.value == 789
    assert triple_child.child.value == 789
    assert triple_child.value == 789
    assert parent.ref_value == 789

    # Reference string should remain unchanged
    assert parent.get_raw_value("ref_value") == "#./child/value"
    assert triple_child.get_raw_value("value") == "#./child/value"
    assert triple_child.child.get_raw_value("value") == "#./child/value"


def test_set_at_reference_allow_non_reference():
    """Test setting a value through a reference with allow_non_reference=True"""
    parent = ParentQuam(child=ChildQuam(value=42), ref_value="#./child/value")
    parent.set_at_reference("ref_value", 789, allow_non_reference=True)
    assert parent.ref_value == 789

    with pytest.raises(ValueError):
        parent.child.set_at_reference("value", 43)

    assert parent.child.value == 789
