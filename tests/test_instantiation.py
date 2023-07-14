import pytest
from typing import List
from copy import deepcopy
from dataclasses import dataclass

from quam_components.core.quam_base import QuamBase, QuamElement
from quam_components.components.superconducting_qubits import Transmon
from quam_components.core.quam_instantiation import get_class_attributes


def test_get_class_attributes():
    @dataclass
    class TestClass(QuamElement):
        a: int
        b: List[int]
        c = 25
        d: str = "hello"

    attr_annotations = get_class_attributes(TestClass)
    assert attr_annotations["required"] == {"a": int, "b": List[int]}
    assert attr_annotations["optional"] == {"d": str, "controller": str}
    assert attr_annotations["allowed"] == {
        "a": int,
        "b": List[int],
        "d": str,
        "controller": str,
    }


def test_get_class_attributes_subclass():
    class AbstractClass(QuamElement):
        elem: float = 42

    @dataclass
    class TestClass(AbstractClass):
        a: int
        b: List[int]
        c = 25
        d: str = "hello"

    attr_annotations = get_class_attributes(TestClass)
    assert attr_annotations["required"] == {"a": int, "b": List[int]}
    assert attr_annotations["optional"] == {"d": str, "elem": float, "controller": str}
    assert attr_annotations["allowed"] == {
        "a": int,
        "b": List[int],
        "d": str,
        "elem": float,
        "controller": str,
    }


quam_dict_single = {
    "qubit": {
        "id": 0,
        # "xy": {
        #     "pi_amp": 10e-3,
        #     "pi_length": 40,
        #     "anharmonicity": 200e6,
        # }
    },
}


class QuamTestSingle(QuamBase):
    qubit: Transmon


def test_instantiation_single_element():
    quam = QuamTestSingle()
    quam.load(quam_dict_single)

    assert isinstance(quam.qubit, Transmon)
    assert quam.qubit.id == 0
    assert quam.qubit.xy is None


quam_dict_single_nested = {
    "qubit": {
        "id": 0,
        "xy": {
            "pi_amp": 10e-3,
            "pi_length": 40,
            "anharmonicity": 200e6,
        },
    },
}


def test_instantiation_single_nested_element():
    quam = QuamTestSingle()
    with pytest.raises(AttributeError):
        quam.load(quam_dict_single_nested)

    quam_dict = deepcopy(quam_dict_single_nested)
    quam_dict["qubit"]["xy"]["mixer"] = {
        "id": 0,
        "local_oscillator": {"power": 10, "frequency": 6e9},
    }
    quam.load(quam_dict)

    assert quam.qubit.xy.mixer.id == 0
    assert quam.qubit.xy.mixer.name == "mixer0"
    assert quam.qubit.xy.mixer.local_oscillator.power == 10
    assert quam.qubit.xy.mixer.local_oscillator.frequency == 6e9


# def test_instantiation_fixed_attrs():
#     ...

# def test_instantiation_unfixed_attrs():
#     ...
