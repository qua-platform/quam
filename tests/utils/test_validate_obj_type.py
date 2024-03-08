import pytest
from typing import List, Dict, Literal

from quam.utils.general import validate_obj_type


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


def test_validate_typing_literal():
    validate_obj_type("a", Literal["a", "b", "c"])
    validate_obj_type("b", Literal["a", "b", "c"])

    with pytest.raises(TypeError):
        validate_obj_type("d", Literal["a", "b", "c"])

    with pytest.raises(TypeError):
        validate_obj_type(123, Literal["b", "c"])
