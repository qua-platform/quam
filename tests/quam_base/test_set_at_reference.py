import pytest
from quam.core.quam_classes import QuamBase, QuamRoot, quam_dataclass


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
    return_val = parent.set_at_reference("ref_value", 123)

    assert return_val == "#./child/value"
    
    # Check that the value was set correctly
    assert parent.child.value == 123
    # Reference string should remain unchanged
    assert parent.get_unreferenced_value("ref_value") == "#./child/value"


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
    assert root.get_unreferenced_value("abs_ref") == "#/parent/child/value"
    assert root.parent.get_unreferenced_value("ref_value") == "#./child/value"


def test_set_at_absolute_reference():
    """Test setting a value through an absolute reference"""
    root = RootQuam(parent=ParentQuam(child=ChildQuam()))
    
    # Set value through absolute reference
    root.set_at_reference("abs_ref", 456)
    
    # Check that the value was set correctly
    assert root.parent.child.value == 456
    # Reference string should remain unchanged
    assert root.get_unreferenced_value("abs_ref") == "#/parent/child/value"


def test_set_at_absolute_reference_invalid():
    """Test handling of invalid absolute references"""
    root = RootQuam(parent=ParentQuam(child=ChildQuam()))
    root.abs_ref = "#/nonexistent/path"
    
    with pytest.raises(AttributeError):
        root.set_at_reference("abs_ref", 456)
