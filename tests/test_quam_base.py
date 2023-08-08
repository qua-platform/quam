from typing import List
from dataclasses import dataclass, fields, is_dataclass, field

from quam_components.core import *


def test_update_quam_component_quam():
    quam_root = QuamRoot()
    assert QuamComponent._quam is quam_root

    quam_component = QuamComponent()
    assert quam_component._quam is quam_root


@dataclass(eq=False)
class QuamTest(QuamRoot):
    int_val: int
    quam_elem: QuamComponent
    quam_elem_list: List[QuamComponent]


def test_iterate_empty_quam_root():
    quam_root = QuamRoot()
    elems = list(quam_root.iterate_components())
    assert len(elems) == 0


def test_iterate_empty_quam_component():
    elem = QuamComponent()
    elems = list(elem.iterate_components())
    assert len(elems) == 1
    assert elems[0] is elem
    assert set(elem.get_attrs()) == set()


def test_iterate_quam_component_nested():
    elem = QuamTest(
        int_val=42, quam_elem=QuamComponent(), quam_elem_list=[QuamComponent()]
    )
    elems = list(elem.iterate_components())
    assert len(elems) == 2
    assert elems[0] is elem.quam_elem
    assert elems[1] is elem.quam_elem_list[0]

    assert set(elem.get_attrs()) == {"int_val", "quam_elem", "quam_elem_list"}


def test_iterate_quam_component_duplicate():
    @dataclass
    class QuamTest(QuamRoot):
        quam_elem1: QuamComponent
        quam_elem2: QuamComponent

    quam_components = [QuamComponent(), QuamComponent()]
    elem = QuamTest(quam_elem1=quam_components[0], quam_elem2=quam_components[1])
    elems = list(elem.iterate_components())
    assert elems == quam_components

    quam_component = QuamComponent()
    elem = QuamTest(quam_elem1=quam_component, quam_elem2=quam_component)
    elems = list(elem.iterate_components())
    assert elems == [quam_component]


def test_iterate_quam_component_list_duplicate():
    @dataclass
    class QuamTest(QuamRoot):
        quam_list: List[QuamComponent]

    quam_components = [QuamComponent(), QuamComponent()]
    elem = QuamTest(quam_list=quam_components)
    elems = list(elem.iterate_components())
    assert elems == quam_components

    quam_component = QuamComponent()
    elem = QuamTest(quam_list=[quam_component, quam_component])
    elems = list(elem.iterate_components())
    assert elems == [quam_component]


def test_iterate_quam_with_elements():
    test_quam = QuamTest(
        int_val=42,
        quam_elem=QuamComponent(),
        quam_elem_list=[QuamComponent(), QuamComponent()],
    )

    elems = list(test_quam.iterate_components())
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


def test_iterate_components_nested():
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

    elems = list(test_quam.iterate_components())
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


def test_iterate_components_dict():
    elem = QuamComponent()
    elem_dict = QuamDictComponent(a=42, b=elem)

    elems = list(elem_dict.iterate_components())

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


def test_to_dict_nondefault():
    @dataclass
    class QuamBasicComponent(QuamComponent):
        required_val: int
        optional_val: int = 42
        optional_list: List[int] = field(default_factory=list)

    quam_component = QuamBasicComponent(required_val=42)
    assert quam_component.to_dict() == {"required_val": 42}
    assert quam_component.to_dict(include_defaults=True) == {
        "required_val": 42,
        "optional_val": 42,
        "optional_list": [],
    }

    quam_component = QuamBasicComponent(required_val=42, optional_val=43)
    assert quam_component.to_dict() == {"required_val": 42, "optional_val": 43}
    assert quam_component.to_dict(include_defaults=True) == {
        "required_val": 42,
        "optional_val": 43,
        "optional_list": [],
    }

    quam_component = QuamBasicComponent(required_val=42, optional_list=["test"])
    assert quam_component.to_dict() == {"required_val": 42, "optional_list": ["test"]}
    assert quam_component.to_dict(include_defaults=True) == {
        "required_val": 42,
        "optional_val": 42,
        "optional_list": ["test"],
    }

    quam_component = QuamBasicComponent(required_val=42)
    quam_component.optional_list.append("test")
    assert quam_component.to_dict() == {"required_val": 42, "optional_list": ["test"]}
    assert quam_component.to_dict(include_defaults=True) == {
        "required_val": 42,
        "optional_val": 42,
        "optional_list": ["test"],
    }
