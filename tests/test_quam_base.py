from typing import List
from dataclasses import dataclass, fields, is_dataclass

from quam_components.core import *


def test_update_quam_element_quam():
    quam_base = QuamBase()
    assert QuamElement._quam is quam_base

    quam_element = QuamElement()
    assert quam_element._quam is quam_base


@dataclass
class QuamTest(QuamBase):
    int_val: int
    quam_elem: QuamElement
    quam_elem_list: List[QuamElement]


def test_iterate_quam_element():
    elem = QuamElement()
    elems = list(iterate_quam_elements(elem))
    assert len(elems) == 1
    assert elems[0] is elem

def test_iterate_quam_element_nested():
    elem = QuamTest(int_val=42, quam_elem=QuamElement(), quam_elem_list=[QuamElement()])
    elems = list(iterate_quam_elements(elem))
    assert len(elems) == 2
    assert elems[0] is elem.quam_elem
    assert elems[1] is elem.quam_elem_list[0]

def test_iterate_quam_with_elements():
    test_quam = QuamTest(
        int_val=42,
        quam_elem=QuamElement(),
        quam_elem_list=[QuamElement(), QuamElement()],
    )

    elems = list(iterate_quam_elements(test_quam))
    assert len(elems) == 3
    assert all(isinstance(elem, QuamElement) for elem in elems)


@dataclass
class QuamElementTest(QuamElement):
    int_val: int
    quam_elem: QuamElement
    quam_elem_list: List[QuamElement]


@dataclass
class NestedQuamTest(QuamBase):
    int_val: int
    quam_elem: QuamElementTest
    quam_elem_list: List[QuamElementTest]


def test_iterate_quam_elements_nested():
    quam_element = QuamElementTest(
        int_val=42,
        quam_elem=QuamElement(),
        quam_elem_list=[QuamElement(), QuamElement()],
    )

    test_quam = NestedQuamTest(
        int_val=42, quam_elem=quam_element, quam_elem_list=[quam_element, quam_element]
    )

    elems = list(iterate_quam_elements(test_quam))
    assert len(elems) == 4
    assert all(isinstance(elem, QuamElement) for elem in elems)


def test_quam_dict_element():
    elem = QuamDictElement(a=42)
    assert isinstance(elem, QuamElement)
    assert is_dataclass(elem)
    assert elem.a == 42
    assert elem._attrs == {"a": 42}

    elem.a = 43
    assert elem.a == 43
    assert elem._attrs == {"a": 43}

    elem.b = 44
    assert elem.b == 44
    assert elem._attrs == {"a": 43}

    elem['c'] = 45
    assert elem.c == 45
    assert elem._attrs == {"a": 43, "c": 45}


def test_iterate_quam_elements_dict():
    elem = QuamElement()
    elem_dict = QuamDictElement(a=42, b=elem)

    elems = list(iterate_quam_elements(elem_dict))
    assert len(elems) == 2
    assert all(isinstance(elem, QuamElement) for elem in elems)
    assert elems[0] is elem_dict
    assert elems[1] is elem_dict.b
    