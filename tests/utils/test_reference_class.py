from typing import Any
import pytest

from quam.core import quam_dataclass
from quam.utils import ReferenceClass


def test_instantiate_reference_class():
    ReferenceClass()


def test_set_non_reference_attribute():
    reference_obj = ReferenceClass()
    reference_obj.test = 42
    assert reference_obj.test == 42


def test_base_reference_class():
    reference_obj = ReferenceClass()

    with pytest.raises(NotImplementedError):
        reference_obj._is_reference("a")

    with pytest.raises(NotImplementedError):
        reference_obj._get_referenced_value("a")

    with pytest.raises(AttributeError):
        reference_obj.a


class SubReferenceClass(ReferenceClass):
    def _is_reference(self, attr: str) -> bool:
        return isinstance(attr, str) and attr.startswith("#")

    def _get_referenced_value(self, attr: str) -> Any:
        return attr[1:]


def test_set_reference_attribute():
    reference_obj = SubReferenceClass()
    reference_obj.a = "#b"
    assert reference_obj.a == "b"

    reference_obj.a = "#c"
    assert reference_obj.a == "c"

    reference_obj.a = 42
    assert reference_obj.a == 42


@quam_dataclass
class SubReferenceDataClass(SubReferenceClass):
    a: float = 42

    def __post_init__(self) -> None:
        super().__init__()


def test_reference_dataclass():
    sub_reference_class = SubReferenceDataClass()
    assert sub_reference_class.a == 42

    sub_reference_class.c = "#d"
    assert sub_reference_class.c == "d"

    sub_reference_class.a = "#b"
    assert sub_reference_class.a == "b"
    assert sub_reference_class.c == "d"
