import pytest

from quam.utils import get_class_from_path


def test_get_transmon_from_class_path():
    transmon_path = "quam.examples.superconducting_qubits.components.Transmon"
    transmon_class = get_class_from_path(transmon_path)
    from quam.examples.superconducting_qubits.components import Transmon

    assert transmon_class == Transmon


def test_get_class_module_not_found_raises():
    with pytest.raises(ModuleNotFoundError):
        get_class_from_path("quam.nonexistent_module.SomeClass")


def test_get_class_not_in_module_raises_attribute_error():
    with pytest.raises(AttributeError, match="'CompletelyUnknownClass'.*not found"):
        get_class_from_path("quam.core.CompletelyUnknownClass")


def test_get_class_not_in_module_names_the_module():
    with pytest.raises(AttributeError, match="quam.core"):
        get_class_from_path("quam.core.CompletelyUnknownClass")


def test_get_class_not_in_module_typo_suggests_close_match():
    # "QuamRooot" is one character off from "QuamRoot"
    with pytest.raises(AttributeError, match="Did you mean"):
        get_class_from_path("quam.core.QuamRooot")


def test_get_class_not_in_module_lists_available_when_no_close_match():
    with pytest.raises(AttributeError, match="Available classes"):
        get_class_from_path("quam.core.XyzCompletelyUnrelated")
