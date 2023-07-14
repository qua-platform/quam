from typing import List, Generator
from dataclasses import dataclass

from quam_components.core import QuamBase, QuamElement, iterate_quam_elements


@dataclass
class TestQuam(QuamBase):
    int_val: int
    quam_elem: QuamElement
    quam_elem_list: List[QuamElement]


def test_iterate_quam_elements():
    test_quam = TestQuam(
        int_val=42,
        quam_elem=QuamElement(),
        quam_elem_list=[QuamElement(), QuamElement()],
    )

    elems = list(iterate_quam_elements(test_quam))
    assert len(elems) == 3
    assert all(isinstance(elem, QuamElement) for elem in elems)


@dataclass
class TestQuamElement(QuamElement):
    int_val: int
    quam_elem: QuamElement
    quam_elem_list: List[QuamElement]


@dataclass
class TestQuamNested(QuamBase):
    int_val: int
    quam_elem: TestQuamElement
    quam_elem_list: List[TestQuamElement]


def test_iterate_quam_elements_nested() -> Generator[QuamElement, None, None]:
    quam_element = TestQuamElement(
        int_val=42,
        quam_elem=QuamElement(),
        quam_elem_list=[QuamElement(), QuamElement()],
    )

    test_quam = TestQuam(
        int_val=42, quam_elem=quam_element, quam_elem_list=[quam_element, quam_element]
    )

    elems = list(iterate_quam_elements(test_quam))
    assert len(elems) == 12
    assert all(isinstance(elem, QuamElement) for elem in elems)
