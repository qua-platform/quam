from dataclasses import dataclass
from quam_components.core.quam_classes import *


def test_basic_list_to_dict():
    l = QuamList([1, 2, 3])
    assert l.to_dict() == [1, 2, 3]


def test_list_with_component_to_dict():
    @dataclass
    class QuamTest(QuamComponent):
        int_val: int

    c = QuamTest(42)
    quam_list = QuamList([c])
    assert quam_list.to_dict() == [{"int_val": 42}]


def test_list_with_component_list_to_dict():
    l1 = QuamList([1, 2, 3])
    l2 = QuamList([1, 2, l1])
    assert l2.to_dict() == [1, 2, [1, 2, 3]]

    l3 = QuamList([1, 2, [4, 5, 6]])
    assert isinstance(l3[2], QuamList)
    assert l3.to_dict() == [1, 2, [4, 5, 6]]