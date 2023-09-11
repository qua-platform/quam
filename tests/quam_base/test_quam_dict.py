import pytest
from typing import Dict
from dataclasses import dataclass, field
from quam_components.core.quam_classes import *
from collections import UserDict


@dataclass
class BareQuamComponent(QuamComponent):
    pass


def test_empty_quam_dict():
    quam_dict = QuamDict()
    assert isinstance(quam_dict, QuamBase)
    assert not isinstance(quam_dict, QuamComponent)
    assert isinstance(quam_dict, UserDict)

    assert quam_dict.data == {}
    assert quam_dict._get_attr_names() == []
    assert quam_dict.get_attrs() == {}
    assert quam_dict.to_dict() == {}

    with pytest.raises(AttributeError):
        quam_dict.nonexisting_attr
    with pytest.raises(KeyError):
        quam_dict["nonexisting_attr"]
    with pytest.raises(AttributeError):
        quam_dict.get_unreferenced_value("nonexisting_attr")

    for val in [42, True, False, None]:
        assert not quam_dict._attr_val_is_default("nonexisting_attr", val)


def test_quam_dict_nonempty():
    quam_dict = QuamDict(val1=42)
    assert quam_dict.data == {"val1": 42}
    assert quam_dict._get_attr_names() == ["val1"]
    assert quam_dict.get_attrs() == {"val1": 42}
    assert quam_dict.to_dict() == {"val1": 42}

    assert quam_dict.val1 == 42
    assert quam_dict["val1"] == 42
    assert quam_dict.get_unreferenced_value("val1") == 42

    for val in [42, True, False, None]:
        assert not quam_dict._attr_val_is_default("val1", val)


def test_quam_dict_adding_elements():
    quam_dict = QuamDict()
    quam_dict["a"] = 42
    assert dict(quam_dict) == {"a": 42}
    assert quam_dict.data == {"a": 42}

    quam_dict["list"] = [1, 2, 3]
    assert dict(quam_dict) == {"a": 42, "list": [1, 2, 3]}
    assert isinstance(quam_dict["list"], QuamList)
    assert quam_dict.data == {"a": 42, "list": [1, 2, 3]}
    assert quam_dict.list == [1, 2, 3]

    quam_dict.pop("list")
    assert dict(quam_dict) == {"a": 42}


def test_quam_dict_setattr():
    quam_dict = QuamDict()

    quam_dict.val1 = 42
    assert quam_dict.val1 == 42
    assert quam_dict.data == {"val1": 42}
    assert quam_dict._get_attr_names() == ["val1"]
    assert quam_dict.get_attrs() == {"val1": 42}
    with pytest.raises(KeyError):
        quam_dict["val2"]
    with pytest.raises(AttributeError):
        quam_dict.get_unreferenced_value("val2")


def test_quam_dict_setitem():
    quam_dict = QuamDict()

    quam_dict["val1"] = 42
    assert quam_dict.val1 == 42
    assert quam_dict.data == {"val1": 42}
    assert quam_dict._get_attr_names() == ["val1"]
    assert quam_dict.get_attrs() == {"val1": 42}
    assert quam_dict.to_dict() == {"val1": 42}
    assert quam_dict["val1"] == 42
    assert quam_dict.get_unreferenced_value("val1") == 42


def test_inner_quam_dict():
    quam_dict = QuamDict(inner_dict={"val1": 42})
    assert isinstance(quam_dict.inner_dict, QuamDict)

    quam_dict = QuamDict(inner_dict={"inner_inner_dict": {"val1": 42}})
    assert isinstance(quam_dict.inner_dict, QuamDict)
    assert isinstance(quam_dict.inner_dict.inner_inner_dict, QuamDict)

    quam_dict = QuamDict()
    quam_dict.inner_dict = {"val1": 42}
    assert isinstance(quam_dict.inner_dict, QuamDict)


def test_dict_from_quam_root():
    @dataclass
    class TestDictQuamRoot(QuamRoot):
        test_dict: dict = field(default_factory=dict)

    quam_root = TestDictQuamRoot()
    assert isinstance(quam_root.test_dict, QuamDict)


def test_dict_from_quam_component():
    @dataclass
    class TestDictQuamComponent(QuamComponent):
        test_dict: dict = field(default_factory=dict)

    quam_component = TestDictQuamComponent()
    assert isinstance(quam_component.test_dict, QuamDict)

    quam_component = TestDictQuamComponent(test_dict={"bla": 42})
    assert isinstance(quam_component.test_dict, QuamDict)
    assert quam_component.test_dict.bla == 42


def test_quam_dict_getattr():
    quam_dict = QuamDict(val1=42)
    assert quam_dict.val1 == 42
    assert hasattr(quam_dict, "val1")
    assert "val1" in quam_dict


def test_quam_dict_get_attr_names():
    quam_dict = QuamDict(val1=42)
    assert quam_dict._get_attr_names() == ["val1"]


def test_val_matches_annotation():
    @dataclass
    class TestQuamComponent(QuamComponent):
        val_dict: dict
        val_float: float
        val_Dict: Dict
        val_Dict_annotated: Dict[str, int]

    assert TestQuamComponent._val_matches_attr_annotation("val_dict", {})
    assert TestQuamComponent._val_matches_attr_annotation("val_dict", {1: 2})
    assert TestQuamComponent._val_matches_attr_annotation("val_dict", QuamDict())
    assert not TestQuamComponent._val_matches_attr_annotation("val_dict", 42)

    assert not TestQuamComponent._val_matches_attr_annotation("val_float", {})
    assert not TestQuamComponent._val_matches_attr_annotation("val_float", {1: 2})
    assert not TestQuamComponent._val_matches_attr_annotation("val_float", QuamDict())
    assert TestQuamComponent._val_matches_attr_annotation("val_float", 42.0)

    assert TestQuamComponent._val_matches_attr_annotation("val_Dict", {})
    assert TestQuamComponent._val_matches_attr_annotation("val_Dict", {1: 2})
    assert TestQuamComponent._val_matches_attr_annotation("val_Dict", QuamDict())
    assert not TestQuamComponent._val_matches_attr_annotation("val_Dict", 42)

    assert TestQuamComponent._val_matches_attr_annotation("val_Dict_annotated", {})
    assert TestQuamComponent._val_matches_attr_annotation("val_Dict_annotated", {1: 2})
    assert TestQuamComponent._val_matches_attr_annotation(
        "val_Dict_annotated", QuamDict()
    )
    assert not TestQuamComponent._val_matches_attr_annotation("val_Dict_annotated", 42)
