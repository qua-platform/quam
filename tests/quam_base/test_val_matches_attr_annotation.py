from typing import Dict, List
from quam.core.quam_classes import *


@quam_dataclass
class QuamTest(QuamComponent):
    int_val: int
    str_val: str


def test_attr_type_nonexisting():
    test_quam = QuamTest(int_val=1, str_val="test")
    assert not test_quam._val_matches_attr_annotation("nonexisting", None)
    assert not test_quam._val_matches_attr_annotation("nonexisting", 123)


def test_attr_type_basic():
    test_quam = QuamTest(int_val=1, str_val="test")
    assert test_quam._val_matches_attr_annotation("int_val", 1)
    assert test_quam._val_matches_attr_annotation("str_val", "hi")
    assert not test_quam._val_matches_attr_annotation("int_val", "hi")
    assert not test_quam._val_matches_attr_annotation("str_val", 1)


@quam_dataclass
class QuamTest2(QuamComponent):
    int_val: int
    str_val: str
    l1: list
    l2: List[int]
    d1: dict
    d2: Dict[str, int]


def test_attr_type_dict():
    test_quam = QuamTest2(
        int_val=1, str_val="test", l1=[1, 2, 3], l2=[1, 2, 3], d1={"a": 1}, d2={"a": 1}
    )
    assert test_quam._val_matches_attr_annotation("d1", {})
    assert test_quam._val_matches_attr_annotation("d2", {})
    assert not test_quam._val_matches_attr_annotation("d1", 42)
    assert not test_quam._val_matches_attr_annotation("d2", 42)


def test_attr_type_list():
    test_quam = QuamTest2(
        int_val=1, str_val="test", l1=[1, 2, 3], l2=[1, 2, 3], d1={"a": 1}, d2={"a": 1}
    )
    assert test_quam._val_matches_attr_annotation("l1", [])
    assert test_quam._val_matches_attr_annotation("l2", [])
    assert not test_quam._val_matches_attr_annotation("l1", 42)
    assert not test_quam._val_matches_attr_annotation("l2", 42)
