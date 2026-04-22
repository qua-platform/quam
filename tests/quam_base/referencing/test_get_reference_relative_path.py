from typing import List, Optional

import pytest

from quam.core import *


@quam_dataclass
class QuamComponentTest(QuamComponent):
    test_str: str
    inner_child: Optional["QuamComponentTest"] = None


@quam_dataclass
class QuamRootTest(QuamRoot):
    quam_elem: QuamComponentTest
    quam_elem_list: List[QuamComponentTest]


@pytest.fixture
def setup_quam_hierarchy():
    nested_child = QuamComponentTest(test_str="hi1")
    child_component = QuamComponentTest(test_str="hi1", inner_child=nested_child)

    child_without_parent = QuamComponentTest(test_str="hi2")

    list_child = QuamComponentTest(test_str="hi3")

    root = QuamRootTest(quam_elem=child_component, quam_elem_list=[list_child])

    return root, child_component, nested_child, child_without_parent, list_child


@pytest.mark.usefixtures("setup_quam_hierarchy")
def test_get_reference_with_attr(setup_quam_hierarchy):
    root, child_component, nested_child, _, _ = setup_quam_hierarchy

    # Test getting reference with attr
    assert (
        child_component.get_reference(attr="inner_child") == "#/quam_elem/inner_child"
    )


def test_get_reference_with_relative_path(setup_quam_hierarchy):
    root, child_component, nested_child, _, _ = setup_quam_hierarchy

    # Test getting reference with relative_path
    assert (
        child_component.get_reference(relative_path="#./inner_child")
        == "#/quam_elem/inner_child"
    )


def test_get_reference_with_both_attr_and_relative_path(setup_quam_hierarchy):
    root, child_component, nested_child, _, _ = setup_quam_hierarchy

    # Test that providing both attr and relative_path raises a ValueError
    with pytest.raises(ValueError):
        child_component.get_reference(
            attr="inner_child", relative_path="#./inner_child"
        )


def test_get_reference_with_invalid_relative_path(setup_quam_hierarchy):
    root, child_component, nested_child, _, _ = setup_quam_hierarchy

    # Test that providing an invalid relative_path raises a ValueError
    with pytest.raises(ValueError):
        child_component.get_reference(relative_path="not_a_reference")


def test_get_reference_without_parent():
    # Create a component without a parent
    orphan_component = QuamComponentTest(test_str="orphan")

    # Test that trying to get a reference without a parent raises an AttributeError
    with pytest.raises(AttributeError):
        orphan_component.get_reference(attr="test_str")


def test_get_reference_with_parent_operator(setup_quam_hierarchy):
    root, child_component, nested_child, _, _ = setup_quam_hierarchy

    # Test getting reference with parent operator
    assert nested_child.get_reference(relative_path="#../") == "#/quam_elem"


def test_get_reference_with_multiple_parent_operators(setup_quam_hierarchy):
    root, child_component, nested_child, _, _ = setup_quam_hierarchy

    # Test getting reference with multiple parent operators
    assert (
        nested_child.get_reference(relative_path="#../../quam_elem_list/0")
        == "#/quam_elem_list/0"
    )


def test_get_reference_with_complex_relative_path(setup_quam_hierarchy):
    root, child_component, nested_child, _, _ = setup_quam_hierarchy

    # Test getting reference with a complex relative path
    assert (
        nested_child.get_reference(relative_path="#../inner_child/../") == "#/quam_elem"
    )
