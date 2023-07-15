from typing import List
from dataclasses import dataclass

from quam_components.core import *


def test_base_quam_element_reference():
    quam_elem = QuamElement()
    quam_elem.a = ":test"
    assert quam_elem._references == {"a": ":test"}


def test_subclass_quam_element_reference():
    @dataclass(kw_only=True, eq=False)
    class QuamElementTest(QuamElement):
        ...

    quam_elem = QuamElementTest()
    quam_elem.a = ":test"
    assert quam_elem._references == {"a": ":test"}


@dataclass(kw_only=True, eq=False)
class QuamElementTest(QuamElement):
    int_val: int


def test_quam_element_reference_after_initialization():
    quam_elem = QuamElementTest(int_val=42)

    quam_elem.int_val = ":test"
    assert quam_elem._references == {"int_val": ":test"}


def test_quam_element_reference_during_initialization():
    quam_elem = QuamElementTest(int_val=":test")
    assert quam_elem._references == {"int_val": ":test"}


def test_basic_reference():
    @dataclass(kw_only=True, eq=False)
    class QuamBaseTest(QuamBase):
        quam_elem1: QuamElementTest
        quam_elem2: QuamElementTest

    quam_elem1 = QuamElementTest(int_val=1)
    quam_elem2 = QuamElementTest(int_val=":quam_elem1.int_val")

    assert quam_elem1._references is not quam_elem2._references
    assert quam_elem2._references == {"int_val": ":quam_elem1.int_val"}

    quam = QuamBaseTest(quam_elem1=quam_elem1, quam_elem2=quam_elem2)

    assert quam_elem1.int_val == 1
    assert quam_elem2.int_val == 1


def test_list_referencing():
    @dataclass(kw_only=True, eq=False)
    class QuamBaseTest(QuamBase):
        quam_elems: List[QuamElementTest]
        quam_elem2: QuamElementTest

    quam_elems = [QuamElementTest(int_val=k) for k in range(5)]
    quam_elem2 = QuamElementTest(int_val=":quam_elems[3].int_val")

    assert quam_elem2._references == {"int_val": ":quam_elems[3].int_val"}

    quam = QuamBaseTest(quam_elems=quam_elems, quam_elem2=quam_elem2)

    for k, elem in enumerate(quam.quam_elems):
        assert elem.int_val == k

    assert quam_elem2.int_val == 3


def test_reference_dict_elem():
    @dataclass(kw_only=True, eq=False)
    class QuamBaseTest(QuamBase):
        quam_elem_dict: dict
        quam_elem2: QuamElementTest

    quam_elem_dict = QuamDictElement(port_I=2)
    quam_elem2 = QuamElementTest(int_val=":quam_elem_dict.port_I")

    assert quam_elem2._references == {"int_val": ":quam_elem_dict.port_I"}

    quam = QuamBaseTest(quam_elem_dict=quam_elem_dict, quam_elem2=quam_elem2)

    assert quam_elem2.int_val == 2


# TODO Test referencing when a quam element is added to a quam
