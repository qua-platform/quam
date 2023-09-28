from dataclasses import dataclass

from quam_components.utils.reference_class import ReferenceClass


def test_instantiate_reference_class():
    ReferenceClass()


def test_set_non_reference_attribute():
    reference_obj = ReferenceClass()
    reference_obj.test = 42
    assert reference_obj.test == 42


def test_set_reference_attribute():
    reference_obj = ReferenceClass()

    reference_obj.a = ":b"
    assert reference_obj.a == "b"

    reference_obj.a = ":c"
    assert reference_obj.a == "c"

    reference_obj.a = 42
    assert reference_obj.a == 42


@dataclass
class SubReferenceDataClass(ReferenceClass):
    a: float = 42

    def __post_init__(self) -> None:
        super().__init__()


def test_reference_dataclass():
    sub_reference_class = SubReferenceDataClass()
    assert sub_reference_class.a == 42

    sub_reference_class.c = ":d"
    assert sub_reference_class.c == "d"

    sub_reference_class.a = ":b"
    assert sub_reference_class.a == "b"
    assert sub_reference_class.c == "d"
