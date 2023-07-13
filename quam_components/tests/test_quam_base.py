from typing import List
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
        quam_elem_list=[QuamElement(), QuamElement()]
    )

    elems = list(iterate_quam_elements(test_quam))
    assert len(elems) == 3
    assert all(isinstance(elem, QuamElement) for elem in elems)

