import pytest
from typing import List, Literal, Optional, Tuple, Union

from pytest_cov.engine import sys

from quam.core import QuamRoot, QuamComponent, quam_dataclass
from quam.core.quam_classes import QuamDict
from quam.examples.superconducting_qubits.components import Transmon
from quam.core.quam_instantiation import *
from quam.utils import get_dataclass_attr_annotations


def test_get_dataclass_attributes():
    @quam_dataclass
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

    @quam_dataclass
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
    @quam_dataclass
    class AbstractClass(QuamComponent):
        elem: float = 42

    @quam_dataclass
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


@quam_dataclass
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
    @quam_dataclass
    class QuamTestComponent(QuamComponent):
        test_str: str

    instantiate_quam_class(QuamTestComponent, {"test_str": "hello"})

    with pytest.raises(TypeError):
        instantiate_quam_class(QuamTestComponent, {"test_str": 0})

    instantiate_quam_class(QuamTestComponent, {"test_str": 0}, validate_type=False)


def test_instantiation_fixed_attrs():
    @quam_dataclass
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
    @quam_dataclass
    class TestComponent(QuamComponent):
        int_val: int

    instantiate_quam_class(TestComponent, {"int_val": 42})
    with pytest.raises(TypeError):
        instantiate_quam_class(TestComponent, {"int_val": None})


def test_instantiate_optional():
    @quam_dataclass
    class TestComponent(QuamComponent):
        int_vals: Optional[List[int]]

    instantiate_quam_class(TestComponent, {"int_vals": [42]})
    instantiate_quam_class(TestComponent, {"int_vals": None})

    with pytest.raises(TypeError):
        instantiate_quam_class(TestComponent, {"int_vals": 42})


def test_instantiate_sublist():
    @quam_dataclass
    class TestQuamSubList(QuamComponent):
        sublist: List[List[float]]

    obj = instantiate_quam_class(TestQuamSubList, {"sublist": [[1, 2, 3], [4, 5, 6]]})

    assert obj.sublist == [[1, 2, 3], [4, 5, 6]]


def test_instantiate_attr_literal():
    attr = instantiate_attr(
        attr_val="a",
        expected_type=Literal["a", "b", "c"],
    )
    assert attr == "a"


def test_instance_attr_literal_fail():
    with pytest.raises(TypeError):
        instantiate_attr(
            attr_val="d",
            expected_type=Literal["a", "b", "c"],
        )

    with pytest.raises(TypeError):
        instantiate_attr(
            attr_val=1,
            expected_type=Literal["a", "b", "c"],
        )


def test_instantiate_tuple():
    @quam_dataclass
    class TestQuamTuple(QuamComponent):
        tuple_val: Tuple[int, str]

    obj = instantiate_quam_class(TestQuamTuple, {"tuple_val": [42, "hello"]})
    assert obj.tuple_val == (42, "hello")


def test_instantiate_dict_referenced():
    attrs = instantiate_attrs_from_dict(
        attr_dict={"test_attr": "#./reference"},
        required_type=Dict[str, QuamComponentTest],
        fix_attrs=True,
        validate_type=True,
    )

    assert attrs == {"test_attr": "#./reference"}


@quam_dataclass
class TestQuamComponent(QuamComponent):
    a: int


def test_instantiate_union_type():
    @quam_dataclass
    class TestQuamUnion(QuamComponent):
        union_val: Union[int, TestQuamComponent]

    obj = instantiate_quam_class(TestQuamUnion, {"union_val": 42})
    assert obj.union_val == 42

    obj = instantiate_quam_class(TestQuamUnion, {"union_val": {"a": 42}})
    assert obj.union_val.a == 42

    with pytest.raises(TypeError):
        instantiate_quam_class(TestQuamUnion, {"union_val": {"a": "42"}})


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_instantiation_pipe_union_type():
    @quam_dataclass
    class TestQuamUnion(QuamComponent):
        union_val: int | TestQuamComponent

    obj = instantiate_quam_class(TestQuamUnion, {"union_val": 42})
    assert obj.union_val == 42

    obj = instantiate_quam_class(TestQuamUnion, {"union_val": {"a": 42}})
    assert obj.union_val.a == 42

    with pytest.raises(TypeError):
        instantiate_quam_class(TestQuamUnion, {"union_val": {"a": "42"}})


def test_instantiation_nested_tuple():
    @quam_dataclass
    class NestedTupleComponent(QuamComponent):
        nested_tuple: Union[List[Tuple[int, str]], List[Tuple[int]]]

    instantiate_quam_class(
        quam_class=NestedTupleComponent,
        contents={"nested_tuple": [[1, "a"], [2, "b"]]},
    )
