from typing import Dict, List
from dataclasses import dataclass
from quam_components.core.quam_classes import *
from quam_components.core.quam_classes import _get_value_annotation


def test_value_annotation_nonexisting():
    @dataclass
    class TestQuam(QuamComponent):
        int_val: int
        str_val: str

    test_quam = TestQuam(1, "test")
    assert _get_value_annotation(test_quam, "nonexisting") is None
    assert _get_value_annotation(test_quam, "int_val") is None
    assert _get_value_annotation(test_quam, "str_val") is None


def test_value_annotation_dict():
    @dataclass
    class TestQuam(QuamComponent):
        int_val: int
        str_val: str
        d1: dict
        d2: Dict[str, int]

    test_quam = TestQuam(1, "test", {"a": 1}, {"a": 1})
    assert _get_value_annotation(test_quam, "d1") is None
    assert _get_value_annotation(test_quam, "str_val") is None
    assert _get_value_annotation(test_quam, "d2") == int


def test_value_annotation_list():
    @dataclass
    class TestQuam(QuamComponent):
        int_val: int
        str_val: str
        l1: list
        l2: List[int]

    test_quam = TestQuam(1, "test", [1, 2, 3], [1, 2, 3])
    assert _get_value_annotation(test_quam, "l1") is None
    assert _get_value_annotation(test_quam, "str_val") is None
    assert _get_value_annotation(test_quam, "l2") == int
