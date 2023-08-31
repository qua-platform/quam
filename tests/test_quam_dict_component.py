import pytest
from dataclasses import dataclass, field
from quam_components.core.quam_classes import *


@dataclass
class BareQuamComponent(QuamComponent):
    pass


def test_empty_quam_dict():
    quam_dict = QuamDictComponent()
    assert isinstance(quam_dict, QuamBase)
    assert isinstance(quam_dict, QuamComponent)

    assert quam_dict._attrs == {}
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
    quam_dict = QuamDictComponent(val1=42)
    assert quam_dict._attrs == {"val1": 42}
    assert quam_dict._get_attr_names() == ["val1"]
    assert quam_dict.get_attrs() == {"val1": 42}
    assert quam_dict.to_dict() == {"val1": 42}

    assert quam_dict.val1 == 42
    assert quam_dict["val1"] == 42
    assert quam_dict.get_unreferenced_value("val1") == 42

    for val in [42, True, False, None]:
        assert not quam_dict._attr_val_is_default("val1", val)


def test_quam_dict_setattr():
    quam_dict = QuamDictComponent()

    quam_dict.val1 = 42
    assert quam_dict.val1 == 42
    assert quam_dict._attrs == {"val1": 42}
    assert quam_dict._get_attr_names() == ["val1"]
    assert quam_dict.get_attrs() == {"val1": 42}
    with pytest.raises(KeyError):
        quam_dict["val2"]
    with pytest.raises(AttributeError):
        quam_dict.get_unreferenced_value("val2")


def test_quam_dict_setitem():
    quam_dict = QuamDictComponent()

    quam_dict["val1"] = 42
    assert quam_dict.val1 == 42
    assert quam_dict._attrs == {"val1": 42}
    assert quam_dict._get_attr_names() == ["val1"]
    assert quam_dict.get_attrs() == {"val1": 42}
    assert quam_dict.to_dict() == {"val1": 42}
    assert quam_dict["val1"] == 42
    assert quam_dict.get_unreferenced_value("val1") == 42


def test_inner_quam_dict():
    quam_dict = QuamDictComponent(inner_dict={"val1": 42})
    assert isinstance(quam_dict.inner_dict, QuamDictComponent)

    quam_dict = QuamDictComponent(inner_dict={"inner_inner_dict": {"val1": 42}})
    assert isinstance(quam_dict.inner_dict, QuamDictComponent)
    assert isinstance(quam_dict.inner_dict.inner_inner_dict, QuamDictComponent)

    quam_dict = QuamDictComponent()
    quam_dict.inner_dict = {"val1": 42}
    assert isinstance(quam_dict.inner_dict, QuamDictComponent)


def test_dict_from_quam_root():
    @dataclass
    class TestDictQuamRoot(QuamRoot):
        test_dict: dict = field(default_factory=dict)

    quam_root = TestDictQuamRoot()
    assert isinstance(quam_root.test_dict, QuamDictComponent)


def test_dict_from_quam_component():
    @dataclass
    class TestDictQuamComponent(QuamComponent):
        test_dict: dict = field(default_factory=dict)

    quam_component = TestDictQuamComponent()
    assert isinstance(quam_component.test_dict, QuamDictComponent)

    quam_component = TestDictQuamComponent(test_dict={"bla": 42})
    assert isinstance(quam_component.test_dict, QuamDictComponent)
    assert quam_component.test_dict.bla == 42


def test_quam_dict_getattr():
    quam_dict = QuamDictComponent(val1=42)
    assert quam_dict.val1 == 42
    assert hasattr(quam_dict, "val1")
    assert "val1" in quam_dict
