from typing import List, Generator
from dataclasses import dataclass

from quam_components.core import QuamBase, QuamElement, iterate_quam_elements


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


def test_iterate_quam_elements():
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


def test_iterate_quam_elements_nested() -> Generator[QuamElement, None, None]:
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
