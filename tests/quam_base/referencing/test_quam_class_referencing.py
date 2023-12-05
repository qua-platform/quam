from typing import List

from quam.core import *


def test_base_quam_component_reference(BareQuamRoot, BareQuamComponent):
    quam_elem = BareQuamComponent()
    quam_elem.a = "#/test"
    assert quam_elem.a == "#/test"

    root = BareQuamRoot()
    root.elem = quam_elem
    assert quam_elem.a == "#/test"

    root.test = 42
    assert quam_elem.a == 42


@quam_dataclass
class QuamComponentTest(QuamComponent):
    int_val: int


def test_quam_component_reference_after_initialization(BareQuamRoot):
    quam_elem = QuamComponentTest(int_val=42)
    assert quam_elem._root is None
    quam_elem.int_val = "#/test"
    assert quam_elem.int_val == "#/test"

    root = BareQuamRoot()
    root.elem = quam_elem
    assert quam_elem.int_val == "#/test"

    root.test = 42
    assert quam_elem.int_val == 42


def test_quam_component_reference_during_initialization(BareQuamRoot):
    quam_elem = QuamComponentTest(int_val="#/test")
    assert quam_elem.int_val == "#/test"

    root = BareQuamRoot()
    root.elem = quam_elem
    assert quam_elem.int_val == "#/test"

    root.test = 42
    assert quam_elem.int_val == 42


def test_basic_reference():
    @quam_dataclass
    class QuamRootTest(QuamRoot):
        quam_elem1: QuamComponentTest
        quam_elem2: QuamComponentTest

    quam_elem1 = QuamComponentTest(int_val=1)
    quam_elem2 = QuamComponentTest(int_val="#/quam_elem1/int_val")

    quam = QuamRootTest(quam_elem1=quam_elem1, quam_elem2=quam_elem2)

    assert quam_elem1.int_val == 1
    assert quam_elem2.int_val == 1

    quam_elem2.int_val = "#/quam_elem1"
    assert list(quam.iterate_components()) == [quam_elem1, quam_elem2]


def test_list_referencing():
    @quam_dataclass
    class QuamRootTest(QuamRoot):
        quam_elems: List[QuamComponentTest]
        quam_elem2: QuamComponentTest

    quam_elems = [QuamComponentTest(int_val=k) for k in range(5)]
    quam_elem2 = QuamComponentTest(int_val="#/quam_elems/3/int_val")

    quam = QuamRootTest(quam_elems=quam_elems, quam_elem2=quam_elem2)

    for k, elem in enumerate(quam.quam_elems):
        assert elem.int_val == k

    assert quam_elem2.int_val == 3


def test_reference_dict_elem():
    @quam_dataclass
    class QuamRootTest(QuamRoot):
        quam_elem_dict: dict
        quam_elem2: QuamComponentTest

    quam_elem_dict = QuamDict(port_I=2)
    quam_elem2 = QuamComponentTest(int_val="#/quam_elem_dict/port_I")

    QuamRootTest(quam_elem_dict=quam_elem_dict, quam_elem2=quam_elem2)

    assert quam_elem2.int_val == 2


# TODO Test referencing when a quam element is added to a quam
