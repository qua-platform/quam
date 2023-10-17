import pytest
from typing import List
from dataclasses import dataclass

from quam.core import QuamRoot, QuamComponent
from quam.components.superconducting_qubits import Transmon
from quam.core.quam_instantiation import *
from quam.utils import (
    get_dataclass_attr_annotations,
    patch_dataclass,
    validate_obj_type,
)

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10


def test_get_dataclass_attributes():
    @dataclass
    class TestClass(QuamComponent):
        a: int
        b: List[int]
        c = 25
        d: str = "hello"

    attr_annotations = get_dataclass_attr_annotations(TestClass)
    assert attr_annotations["required"] == {"a": int, "b": List[int]}
    assert attr_annotations["optional"] == {
        "d": str,
    }
    assert attr_annotations["allowed"] == {
        "a": int,
        "b": List[int],
        "d": str,
    }


def test_get_dataclass_attributes_subclass():
    class AbstractClass(QuamComponent):
        elem: float = 42

    @dataclass
    class TestClass(AbstractClass):
        a: int
        b: List[int]
        c = 25
        d: str = "hello"

    attr_annotations = get_dataclass_attr_annotations(TestClass)
    assert attr_annotations["required"] == {"a": int, "b": List[int]}
    assert attr_annotations["optional"] == {"d": str, "elem": float}
    assert attr_annotations["allowed"] == {
        "a": int,
        "b": List[int],
        "d": str,
        "elem": float,
    }


def test_get_dataclass_attributes_subdataclass():
    @dataclass(kw_only=True)
    class AbstractClass(QuamComponent):
        elem: float = 42

    @dataclass
    class TestClass(AbstractClass):
        a: int
        b: List[int]
        c = 25
        d: str = "hello"

    attr_annotations = get_dataclass_attr_annotations(TestClass)
    assert attr_annotations["required"] == {"a": int, "b": List[int]}
    assert attr_annotations["optional"] == {"d": str, "elem": float}
    assert attr_annotations["allowed"] == {
        "a": int,
        "b": List[int],
        "d": str,
        "elem": float,
    }


def test_validate_standard_types():
    validate_obj_type(1, int)
    validate_obj_type(1.0, float)
    validate_obj_type("hello", str)
    validate_obj_type(":reference", str)
    validate_obj_type([1, 2, 3], list)
    validate_obj_type((1, 2, 3), tuple)
    validate_obj_type({"a": 1, "b": 2}, dict)
    validate_obj_type(True, bool)
    validate_obj_type(None, type(None))

    with pytest.raises(TypeError):
        validate_obj_type(1, str)
    with pytest.raises(TypeError):
        validate_obj_type("hello", int)


def test_validate_type_exceptions():
    validate_obj_type("#/reference", int)
    validate_obj_type("#/reference", str)
    validate_obj_type("#./reference", int)
    validate_obj_type("#./reference", str)
    validate_obj_type("#../reference", int)
    validate_obj_type("#../reference", str)

    validate_obj_type(None, int)
    validate_obj_type(None, str)


def test_validate_typing_list():
    validate_obj_type([1, 2, 3], List[int])
    with pytest.raises(TypeError):
        validate_obj_type([1, 2, 3], List[str])

    validate_obj_type([1, 2, 3], List)
    validate_obj_type(["a", "b", "c"], List)
    validate_obj_type(["a", "b", "c"], List[str])
    with pytest.raises(TypeError):
        validate_obj_type(["a", "b", "c"], List[int])


def test_validate_typing_dict():
    validate_obj_type({"a": 1, "b": 2}, dict)
    validate_obj_type({"a": 1, "b": 2}, Dict[str, int])
    with pytest.raises(TypeError):
        validate_obj_type({"a": 1, "b": 2}, Dict[str, str])

    validate_obj_type("#/reference", Dict[str, int])
    validate_obj_type("#./reference", Dict[str, int])
    validate_obj_type("#../reference", Dict[str, int])


@dataclass
class QuamComponentTest(QuamComponent):
    test_str: str


def test_instantiate_from_empty_dict():
    obj = instantiate_attrs_from_dict(attr_dict={}, required_type=dict)
    assert obj == {}


def test_instantiate_from_basic_dict():
    obj = instantiate_attrs_from_dict(
        attr_dict={"test_str": "hello"}, required_type=dict
    )
    assert obj == {"test_str": "hello"}


def test_instantiate_from_basic_typing_dict():
    obj = instantiate_attrs_from_dict(
        attr_dict={"test_str": "hello"}, required_type=Dict[str, str]
    )
    assert obj == {"test_str": "hello"}

    with pytest.raises(TypeError):
        instantiate_attrs_from_dict(
            attr_dict={"test_str": "hello"}, required_type=Dict[str, int]
        )


def test_instantiate_from_quam_component_typing_dict():
    quam_dict = {"test_attr": {}}
    with pytest.raises(AttributeError):
        instantiate_attrs_from_dict(
            attr_dict=quam_dict,
            required_type=Dict[str, QuamComponentTest],
        )

    quam_dict = {"test_attr": {"test_str": "hello"}}
    obj = instantiate_attrs_from_dict(
        attr_dict=quam_dict,
        required_type=Dict[str, QuamComponentTest],
    )
    assert isinstance(obj, dict)
    assert isinstance(obj["test_attr"], QuamComponentTest)
    assert obj["test_attr"].test_str == "hello"


def test_instantiate_from_empty_list():
    obj = instantiate_attrs_from_list(attr_list=[], required_type=list)
    assert obj == []


def test_instantiate_from_basic_list():
    obj = instantiate_attrs_from_list(attr_list=["hello", "world"], required_type=list)
    assert obj == ["hello", "world"]


def test_instantiate_from_basic_typing_list():
    obj = instantiate_attrs_from_list(
        attr_list=["hello", "world"], required_type=List[str]
    )
    assert obj == ["hello", "world"]

    with pytest.raises(TypeError):
        instantiate_attrs_from_list(
            attr_list=["hello", "world"], required_type=List[int]
        )


def test_instantiate_from_quam_component_typing_list():
    quam_list = [{}]
    with pytest.raises(AttributeError):
        instantiate_attrs_from_list(
            attr_list=quam_list,
            required_type=List[QuamComponentTest],
        )

    quam_list = [{"test_str": "hello"}, {"test_str": "world"}]
    obj = instantiate_attrs_from_list(
        attr_list=quam_list,
        required_type=List[QuamComponentTest],
    )
    assert isinstance(obj, list)
    assert isinstance(obj[0], QuamComponentTest)
    assert obj[0].test_str == "hello"
    assert isinstance(obj[1], QuamComponentTest)
    assert obj[1].test_str == "world"


def test_instantiate_attr_reference():
    obj = instantiate_attr(attr_val="#/reference", expected_type=str)
    assert obj == "#/reference"

    obj = instantiate_attr(attr_val="#/reference", expected_type=int)
    assert obj == "#/reference"


def test_instantiate_attr_None():
    with pytest.raises(TypeError):
        instantiate_attr(attr_val=None, expected_type=str)

    obj = instantiate_attr(attr_val=None, expected_type=str, validate_type=False)
    assert obj is None

    obj = instantiate_attr(attr_val=None, expected_type=str, allow_none=True)
    assert obj is None


def test_instantiate_other_typing():
    with pytest.raises(TypeError):
        instantiate_attr(attr_val=1, expected_type=typing.Union)

    obj = instantiate_attr(attr_val=1, expected_type=typing.Union, validate_type=False)
    assert obj == 1


def test_instantiate_quam_component_attr():
    contents = {}
    with pytest.raises(AttributeError):
        instantiate_attr(contents, expected_type=QuamComponentTest)

    contents = {"test_str": "hello"}
    obj = instantiate_attr(contents, expected_type=QuamComponentTest)
    assert isinstance(obj, QuamComponentTest)
    assert obj.test_str == "hello"


def test_instantiate_attrs():
    attr_annotations = get_dataclass_attr_annotations(QuamComponentTest)
    assert attr_annotations["required"] == {"test_str": str}

    attrs = instantiate_attrs(
        attr_annotations=attr_annotations,
        contents={"test_str": "hello"},
        fix_attrs=True,
    )
    assert attrs["required"] == {"test_str": "hello"}

    with pytest.raises(AttributeError):
        instantiate_attrs(
            attr_annotations=attr_annotations,
            contents={"test_str": "hello", "extra": 42},
            fix_attrs=True,
        )

    attrs = instantiate_attrs(
        attr_annotations=attr_annotations,
        contents={"test_str": "hello", "extra": 42},
        fix_attrs=False,
    )
    assert attrs["required"] == {"test_str": "hello"}
    assert attrs["extra"] == {"extra": 42}


def test_instantiate_wrong_type():
    class QuamTest(QuamRoot):
        qubit: Transmon

    with pytest.raises(TypeError):
        QuamTest.load({"qubit": 0})


def test_instantiate_component_wrong_type():
    @dataclass
    class QuamTestComponent(QuamComponent):
        test_str: str

    instantiate_quam_class(QuamTestComponent, {"test_str": "hello"})

    with pytest.raises(TypeError):
        instantiate_quam_class(QuamTestComponent, {"test_str": 0})

    instantiate_quam_class(QuamTestComponent, {"test_str": 0}, validate_type=False)


def test_instantiation_fixed_attrs():
    @dataclass
    class TestComponent(QuamComponent):
        int_val: int

    quam_element = instantiate_quam_class(TestComponent, {"int_val": 42})
    assert quam_element.int_val == 42

    with pytest.raises(AttributeError):
        instantiate_quam_class(TestComponent, {"int_val": 42, "extra": 43})

    quam_element = instantiate_quam_class(
        TestComponent, {"int_val": 42, "extra": 43}, fix_attrs=False
    )
    assert quam_element.int_val == 42
    assert quam_element.extra == 43


def test_instantiate_required_cannot_be_None():
    @dataclass
    class TestComponent(QuamComponent):
        int_val: int

    instantiate_quam_class(TestComponent, {"int_val": 42})
    with pytest.raises(TypeError):
        instantiate_quam_class(TestComponent, {"int_val": None})
