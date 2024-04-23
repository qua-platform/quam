from dataclasses import field
from typing import List, Optional
from quam.core.quam_classes import *


def test_basic_list_to_dict():
    l = QuamList([1, 2, 3])
    assert l.to_dict() == [1, 2, 3]


@quam_dataclass
class QuamTest(QuamComponent):
    int_val: int


def test_list_with_component_to_dict():
    c = QuamTest(int_val=42)
    quam_list = QuamList([c])
    assert quam_list.to_dict() == [
        {"int_val": 42, "__class__": "test_to_dict.QuamTest"}
    ]


def test_list_with_component_list_to_dict():
    l1 = QuamList([1, 2, 3])
    l2 = QuamList([1, 2, l1])
    assert l2.to_dict() == [1, 2, [1, 2, 3]]

    l3 = QuamList([1, 2, [4, 5, 6]])
    assert isinstance(l3[2], QuamList)
    assert l3.to_dict() == [1, 2, [4, 5, 6]]


def test_basic_dict_to_dict():
    d = QuamDict({"a": 1, "b": 2, "c": 3})
    assert d.to_dict() == {"a": 1, "b": 2, "c": 3}


def test_dict_with_component_to_dict():
    c = QuamTest(int_val=42)
    quam_dict = QuamDict({"a": c})
    assert quam_dict.to_dict() == {
        "a": {"int_val": 42, "__class__": "test_to_dict.QuamTest"}
    }


@quam_dataclass
class QuamBasicComponent(QuamComponent):
    a: int
    b: str


def test_quam_component_to_dict_basic():
    elem = QuamBasicComponent(a=42, b="foo")

    assert elem.to_dict() == {"a": 42, "b": "foo"}


def test_quam_component_to_dict_nested():
    @quam_dataclass
    class QuamNestedComponent(QuamComponent):
        a: int
        b: str
        c: QuamComponent

    nested_elem = QuamBasicComponent(a=42, b="foo")
    elem = QuamNestedComponent(a=42, b="foo", c=nested_elem)

    assert elem.to_dict() == {
        "a": 42,
        "b": "foo",
        "c": {"a": 42, "b": "foo", "__class__": "test_to_dict.QuamBasicComponent"},
    }


def test_to_dict_nondefault():
    @quam_dataclass
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


def test_omit_default_dict_field():
    @quam_dataclass
    class QuamBasicComponent(QuamComponent):
        d: dict = field(default_factory=dict)

    quam_component = QuamBasicComponent()
    assert quam_component.to_dict() == {}


def test_omit_default_list_field():
    @quam_dataclass
    class QuamBasicComponent(QuamComponent):
        l: list = field(default_factory=list)

    quam_component = QuamBasicComponent()
    assert quam_component.to_dict() == {}


def test_optional_list_to_dict():
    @quam_dataclass
    class QuamBasicComponent(QuamComponent):
        l: Optional[List[int]] = None

    quam_component = QuamBasicComponent()
    assert quam_component.to_dict() == {}

    quam_component = QuamBasicComponent(l=[1, 2, 3])
    assert quam_component.to_dict() == {"l": [1, 2, 3]}


def test_list_to_dict_nondefault():
    @quam_dataclass
    class QuamBasicComponent(QuamComponent):
        l: int = 42

    quam_component = QuamBasicComponent(l=[1, 2, 3])
    assert quam_component.to_dict() == {"l": [1, 2, 3]}
