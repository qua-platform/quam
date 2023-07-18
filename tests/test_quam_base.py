from typing import List
from dataclasses import dataclass, fields, is_dataclass

from quam_components.core import *


def test_update_quam_component_quam():
    quam_base = QuamRoot()
    assert QuamComponent._quam is quam_base

    quam_component = QuamComponent()
    assert quam_component._quam is quam_base


@dataclass
class QuamTest(QuamRoot):
    int_val: int
    quam_elem: QuamComponent
    quam_elem_list: List[QuamComponent]


def test_iterate_quam_component():
    elem = QuamComponent()
    elems = list(iterate_quam_components(elem))
    assert len(elems) == 1
    assert elems[0] is elem
    assert set(get_attrs(elem)) == set()


def test_iterate_quam_component_nested():
    elem = QuamTest(
        int_val=42, quam_elem=QuamComponent(), quam_elem_list=[QuamComponent()]
    )
    elems = list(iterate_quam_components(elem))
    assert len(elems) == 2
    assert elems[0] is elem.quam_elem
    assert elems[1] is elem.quam_elem_list[0]

    assert set(get_attrs(elem)) == {"int_val", "quam_elem", "quam_elem_list"}


def test_iterate_quam_with_elements():
    test_quam = QuamTest(
        int_val=42,
        quam_elem=QuamComponent(),
        quam_elem_list=[QuamComponent(), QuamComponent()],
    )

    elems = list(iterate_quam_components(test_quam))
    assert len(elems) == 3
    assert all(isinstance(elem, QuamComponent) for elem in elems)


@dataclass
class QuamComponentTest(QuamComponent):
    int_val: int
    quam_elem: QuamComponent
    quam_elem_list: List[QuamComponent]


@dataclass
class NestedQuamTest(QuamRoot):
    int_val: int
    quam_elem: QuamComponentTest
    quam_elem_list: List[QuamComponentTest]


def test_iterate_quam_components_nested():
    quam_component = QuamComponentTest(
        int_val=42,
        quam_elem=QuamComponent(),
        quam_elem_list=[QuamComponent(), QuamComponent()],
    )

    test_quam = NestedQuamTest(
        int_val=42,
        quam_elem=quam_component,
        quam_elem_list=[quam_component, quam_component],
    )

    elems = list(iterate_quam_components(test_quam))
    assert len(elems) == 4
    assert all(isinstance(elem, QuamComponent) for elem in elems)


def test_quam_dict_element():
    elem = QuamDictComponent(a=42)
    assert isinstance(elem, QuamComponent)
    assert is_dataclass(elem)
    assert elem.a == 42
    assert elem._attrs == {"a": 42}

    elem.a = 43
    assert elem.a == 43
    assert elem._attrs == {"a": 43}

    elem.b = 44
    assert elem.b == 44
    assert elem._attrs == {"a": 43}

    elem["c"] = 45
    assert elem.c == 45
    assert elem._attrs == {"a": 43, "c": 45}


def test_iterate_quam_components_dict():
    elem = QuamComponent()
    elem_dict = QuamDictComponent(a=42, b=elem)

    elems = list(iterate_quam_components(elem_dict))

    assert len(elems) == 2
    assert all(isinstance(elem, QuamComponent) for elem in elems)
    assert elems[0] is elem_dict
    assert elems[1] is elem_dict.b


def test_nested_quam_dict_explicit():
    elem = QuamDictComponent(subdict=QuamDictComponent(a=42))

    assert elem.subdict.a == 42
    assert elem.subdict._attrs == {"a": 42}
    assert isinstance(elem.subdict, QuamDictComponent)


def test_nested_quam_dict():
    elem = QuamDictComponent(subdict=dict(a=42))

    assert elem.subdict.a == 42
    assert elem.subdict._attrs == {"a": 42}
    assert isinstance(elem.subdict, QuamDictComponent)

    assert elem.to_dict() == {"subdict": {"a": 42}}


@dataclass
class QuamBasicComponent(QuamComponent):
    a: int
    b: str


def test_quam_component_to_dict_basic():
    elem = QuamBasicComponent(a=42, b="foo")

    assert elem.to_dict() == {"a": 42, "b": "foo"}


def test_quam_component_to_dict_nested():
    @dataclass
    class QuamNestedComponent(QuamComponent):
        a: int
        b: str
        c: QuamComponent

    nested_elem = QuamBasicComponent(a=42, b="foo")
    elem = QuamNestedComponent(a=42, b="foo", c=nested_elem)

    assert elem.to_dict() == {"a": 42, "b": "foo", "c": {"a": 42, "b": "foo"}}
