import pytest
import warnings
from dataclasses import field
from typing import Any

from quam.core import QuamRoot, QuamComponent, quam_dataclass
from quam.utils.exceptions import InvalidReferenceError


@quam_dataclass
class MyChild(QuamComponent):
    value: int = 0
    ref_value: Any = "#./value"  # Valid internal reference
    invalid_ref: str = "#./nonexistent"
    invalid_absolute_ref: str = "#/nonexistent"


@quam_dataclass
class MyRoot(QuamRoot):
    child: MyChild = field(default_factory=MyChild)
    nonexistent_in_root: str = "#/other_child"  # Invalid absolute reference


@pytest.fixture
def mock_config(monkeypatch):
    """Fixture to mock get_quam_config and control raise_error_missing_reference."""

    def _mock_config(raise_error: bool):
        # Create a simple mock object with the required attribute
        class MockQuamConfig:
            def __init__(self, raise_err):
                self.raise_error_missing_reference = raise_err

        mock_instance = MockQuamConfig(raise_error)
        monkeypatch.setattr(
            "quam.core.quam_classes.get_quam_config", lambda: mock_instance
        )
        return mock_instance  # Return the mock instance

    return _mock_config


# Test case for raising InvalidReferenceError
def test_missing_reference_raises_error(mock_config):
    mock_config(raise_error=True)
    root = MyRoot()

    # Test invalid relative reference within a component
    with pytest.raises(InvalidReferenceError, match="Could not get reference"):
        _ = root.child.invalid_ref

    # Test invalid absolute reference within a component
    with pytest.raises(InvalidReferenceError, match="Could not get reference"):
        _ = root.child.invalid_absolute_ref

    # Test invalid absolute reference from root
    with pytest.raises(InvalidReferenceError, match="Could not get reference"):
        _ = root.nonexistent_in_root


# Test case for emitting UserWarning
def test_missing_reference_warns(mock_config):
    mock_config(raise_error=False)
    root = MyRoot()

    # Test invalid relative reference within a component
    with pytest.warns(UserWarning, match="Could not get reference"):
        val = root.child.invalid_ref
    # Check that the raw reference string is returned
    assert val == "#./nonexistent"

    # Test invalid absolute reference within a component
    with pytest.warns(UserWarning, match="Could not get reference"):
        val = root.child.invalid_absolute_ref
    assert val == "#/nonexistent"

    # Test invalid absolute reference from root
    with pytest.warns(UserWarning, match="Could not get reference"):
        val = root.nonexistent_in_root
    assert val == "#/other_child"


# Test case for valid reference (should not raise or warn regardless of config)
def test_valid_reference_no_error_or_warning(mock_config):
    # Test with raise_error=True
    mock_config(raise_error=True)
    root_err = MyRoot()
    assert root_err.child.ref_value == 0

    # Test with raise_error=False
    mock_config(raise_error=False)
    root_warn = MyRoot()
    # No warning should be emitted
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # Treat warnings as errors
        assert root_warn.child.ref_value == 0
