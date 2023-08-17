import pytest
from dataclasses import dataclass
from quam_components.core.quam_classes import (
    QuamBase,
    QuamComponent,
    QuamDictComponent,
)


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
    assert quam_dict._attrs == {}
    assert quam_dict._get_attr_names() == []
    assert quam_dict.get_attrs() == {}
    with pytest.raises(KeyError):
        quam_dict["val1"]
    with pytest.raises(AttributeError):
        quam_dict.get_unreferenced_value("val1")


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
