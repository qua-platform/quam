from typing import List
from dataclasses import is_dataclass, field
import pytest

from quam.core import *


def test_error_create_base_classes_directly():
    for cls in [QuamBase, QuamRoot, QuamComponent]:
        with pytest.raises(TypeError) as exc_info:
            cls()
        error_message = (
            f"Cannot instantiate {cls.__name__} directly. Please create a subclass and"
            " make it a dataclass."
        )
        assert str(exc_info.value) == error_message


def test_create_dataclass_subclass():
    for cls in [QuamBase, QuamRoot, QuamComponent]:

        @quam_dataclass
        class TestClass(cls):
            pass

        test_class = TestClass()
        assert isinstance(test_class, cls)
        assert is_dataclass(test_class)


@quam_dataclass
class BareQuamRoot(QuamRoot):
    pass


@quam_dataclass
class BareQuamComponent(QuamComponent):
    pass


def test_update_quam_component_quam():
    quam_root = BareQuamRoot()
    assert QuamComponent._root is quam_root

    quam_component = BareQuamComponent()
    assert quam_component._root is quam_root


@quam_dataclass(eq=False)
class QuamTest(QuamRoot):
    int_val: int
    quam_elem: QuamComponent
    quam_elem_list: List[QuamComponent]


def test_iterate_empty_quam_root():
    quam_root = BareQuamRoot()
    elems = list(quam_root.iterate_components())
    assert len(elems) == 0


def test_iterate_quam_root():
    quam_root = QuamTest(int_val=42, quam_elem=BareQuamComponent(), quam_elem_list=[])
    elems = list(quam_root.iterate_components())
    assert elems == [quam_root.quam_elem]

    quam_root.quam_elem_list.append(BareQuamComponent())
    elems = list(quam_root.iterate_components())
    assert elems == [quam_root.quam_elem, quam_root.quam_elem_list[0]]


def test_iterate_empty_quam_component():
    elem = BareQuamComponent()
    elems = list(elem.iterate_components())
    assert len(elems) == 1
    assert elems[0] is elem
    assert set(elem.get_attrs()) == set()


def test_iterate_quam_component_nested():
    elem = QuamTest(
        int_val=42, quam_elem=BareQuamComponent(), quam_elem_list=[BareQuamComponent()]
    )
    elems = list(elem.iterate_components())
    assert len(elems) == 2
    assert elems[0] is elem.quam_elem
    assert elems[1] is elem.quam_elem_list[0]

    assert set(elem.get_attrs()) == {"int_val", "quam_elem", "quam_elem_list"}


def test_iterate_quam_component_duplicate():
    @quam_dataclass
    class QuamTest(QuamRoot):
        quam_elem1: QuamComponent
        quam_elem2: QuamComponent

    components = [BareQuamComponent(), BareQuamComponent()]
    elem = QuamTest(quam_elem1=components[0], quam_elem2=components[1])
    elems = list(elem.iterate_components())
    assert elems == components

    quam_component = BareQuamComponent()
    elem = QuamTest(quam_elem1=quam_component, quam_elem2=quam_component)
    elems = list(elem.iterate_components())
    assert elems == [quam_component]


def test_iterate_quam_component_list_duplicate():
    @quam_dataclass
    class QuamTest(QuamRoot):
        quam_list: List[QuamComponent]

    components = [BareQuamComponent(), BareQuamComponent()]
    elem = QuamTest(quam_list=components)
    elems = list(elem.iterate_components())
    assert elems == components

    quam_component = BareQuamComponent()
    elem = QuamTest(quam_list=[quam_component, quam_component])
    elems = list(elem.iterate_components())
    assert elems == [quam_component]


def test_iterate_quam_with_elements():
    test_quam = QuamTest(
        int_val=42,
        quam_elem=BareQuamComponent(),
        quam_elem_list=[BareQuamComponent(), BareQuamComponent()],
    )

    elems = list(test_quam.iterate_components())
    assert len(elems) == 3
    assert all(isinstance(elem, QuamComponent) for elem in elems)


@quam_dataclass
class QuamComponentTest(QuamComponent):
    int_val: int
    quam_elem: QuamComponent
    quam_elem_list: List[QuamComponent]


@quam_dataclass
class NestedQuamTest(QuamRoot):
    int_val: int
    quam_elem: QuamComponentTest
    quam_elem_list: List[QuamComponentTest]


def test_iterate_components_nested():
    quam_component = QuamComponentTest(
        int_val=42,
        quam_elem=BareQuamComponent(),
        quam_elem_list=[BareQuamComponent(), BareQuamComponent()],
    )

    with pytest.raises(AttributeError):
        test_quam = NestedQuamTest(
            int_val=42,
            quam_elem=quam_component,
            quam_elem_list=[quam_component, quam_component],
        )

    quam_component.parent = None
    quam_component2 = QuamComponentTest(
        int_val=42,
        quam_elem=BareQuamComponent(),
        quam_elem_list=[BareQuamComponent(), BareQuamComponent()],
    )
    test_quam = NestedQuamTest(
        int_val=42,
        quam_elem=quam_component,
        quam_elem_list=[quam_component2, quam_component2],
    )

    elems = list(test_quam.iterate_components())
    assert len(elems) == 8
    assert all(isinstance(elem, QuamComponent) for elem in elems)


def test_quam_dict_element():
    elem = QuamDict(a=42)
    assert not isinstance(elem, QuamComponent)
    assert isinstance(elem, QuamBase)
    assert is_dataclass(elem)
    assert elem.a == 42
    assert elem.data == {"a": 42}

    elem.a = 43
    assert elem.a == 43
    assert elem.data == {"a": 43}

    elem.b = 44
    assert elem.b == 44
    assert elem.data == {"a": 43, "b": 44}

    elem["c"] = 45
    assert elem.c == 45
    assert elem.data == {"a": 43, "b": 44, "c": 45}


def test_iterate_components_dict():
    elem = BareQuamComponent()
    elem_dict = QuamDict(a=42, b=elem)

    elems = list(elem_dict.iterate_components())

    assert len(elems) == 1
    assert elems[0] is elem_dict.b


def test_nested_quam_dict_explicit():
    elem = QuamDict(subdict=QuamDict(a=42))

    assert elem.subdict.a == 42
    assert elem.subdict.data == {"a": 42}
    assert isinstance(elem.subdict, QuamDict)


def test_nested_quam_dict():
    elem = QuamDict(subdict=dict(a=42))

    assert elem.subdict.a == 42
    assert elem.subdict.data == {"a": 42}
    assert isinstance(elem.subdict, QuamDict)

    assert elem.to_dict() == {"subdict": {"a": 42}}


def test_quam_setattr_quam_dict_component():
    @quam_dataclass
    class TestQuamRoot(QuamRoot):
        quam_dict: dict = field(default_factory=dict)

    quam = TestQuamRoot()
    assert isinstance(quam.quam_dict, QuamDict)

    quam.quam_dict = {"a": 42}
    assert isinstance(quam.quam_dict, QuamDict)
    assert quam.quam_dict.a == 42

    quam.quam_dict = {"a": {"b": 43}}
    assert isinstance(quam.quam_dict, QuamDict)
    assert isinstance(quam.quam_dict.a, QuamDict)
    assert quam.quam_dict.a.b == 43


def test_parent_attr_name(BareQuamComponent):
    inner_quam_component = BareQuamComponent()
    assert inner_quam_component.parent is None
    with pytest.raises(AttributeError):
        inner_quam_component.parent.get_attr_name(inner_quam_component)

    @quam_dataclass
    class OuterQuamComponent(QuamComponent):
        quam_component: QuamComponent

    outer_quam_component = OuterQuamComponent(quam_component=inner_quam_component)
    assert outer_quam_component.quam_component is inner_quam_component
    assert inner_quam_component.parent is outer_quam_component
    assert (
        inner_quam_component.parent.get_attr_name(inner_quam_component)
        == "quam_component"
    )

    outer_quam_component.quam_component = None
    with pytest.raises(AttributeError):
        inner_quam_component.parent.get_attr_name(inner_quam_component)
