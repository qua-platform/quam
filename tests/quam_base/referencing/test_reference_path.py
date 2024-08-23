from typing import List

import pytest

from quam.core import *


def test_root_reference(BareQuamRoot):
    root = BareQuamRoot()
    assert root._root is root

    assert root.get_reference() == "#"


@quam_dataclass
class QuamComponentTest(QuamComponent):
    test_str: str


@quam_dataclass
class QuamRootTest(QuamRoot):
    quam_elem: QuamComponentTest
    quam_elem_list: List[QuamComponentTest]


def test_quam_component_no_parent_reference_error():
    quam_elem = QuamComponentTest(test_str="hi")
    with pytest.raises(AttributeError):
        quam_elem.get_reference()


def test_quam_component_reference():
    root = QuamRootTest(quam_elem=QuamComponentTest(test_str="hi"), quam_elem_list=[])

    assert root.get_reference() == "#"
    assert root.quam_elem.get_reference() == "#/quam_elem"


def test_quam_list_reference():
    root = QuamRootTest(
        quam_elem=QuamComponentTest(test_str="hi"),
        quam_elem_list=[
            QuamComponentTest(test_str="hi"),
            QuamComponentTest(test_str=QuamComponentTest(test_str="hi")),
        ],
    )

    assert root.get_reference() == "#"
    assert root.quam_elem.get_reference() == "#/quam_elem"
    assert root.quam_elem_list[0].get_reference() == "#/quam_elem_list/0"
    assert root.quam_elem_list[1].get_reference() == "#/quam_elem_list/1"
    assert (
        root.quam_elem_list[1].test_str.get_reference() == "#/quam_elem_list/1/test_str"
    )


def test_get_reference_attr():
    component = QuamComponentTest(test_str="hi")
    root = QuamRootTest(quam_elem=component, quam_elem_list=[])
    assert component.get_reference() == "#/quam_elem"
    assert component.get_reference("test_str") == "#/quam_elem/test_str"
