import pytest
from typing import List
from copy import deepcopy
from dataclasses import dataclass

from quam_components.core.quam_base import QuamBase, QuamComponent
from quam_components.components.superconducting_qubits import Transmon
from quam_components.core.quam_instantiation import *


def test_get_class_attributes():
    @dataclass
    class TestClass(QuamComponent):
        a: int
        b: List[int]
        c = 25
        d: str = "hello"

    attr_annotations = get_class_attributes(TestClass)
    assert attr_annotations["required"] == {"a": int, "b": List[int]}
    assert attr_annotations["optional"] == {"d": str,}
    assert attr_annotations["allowed"] == {
        "a": int,
        "b": List[int],
        "d": str,
    }


def test_get_class_attributes_subclass():
    class AbstractClass(QuamComponent):
        elem: float = 42

    @dataclass
    class TestClass(AbstractClass):
        a: int
        b: List[int]
        c = 25
        d: str = "hello"

    attr_annotations = get_class_attributes(TestClass)
    assert attr_annotations["required"] == {"a": int, "b": List[int]}
    assert attr_annotations["optional"] == {"d": str, "elem": float}
    assert attr_annotations["allowed"] == {
        "a": int,
        "b": List[int],
        "d": str,
        "elem": float,
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


@dataclass
class QuamTestSingle(QuamBase):
    qubit: Transmon


def test_instantiation_single_element():
    quam = QuamTestSingle.load(quam_dict_single)

    assert isinstance(quam.qubit, Transmon)
    assert quam.qubit.id == 0
    assert quam.qubit.xy is None

    assert quam.qubit._quam is quam


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

    with pytest.raises(AttributeError):
        quam = QuamTestSingle.load(quam_dict_single_nested)

    quam_dict = deepcopy(quam_dict_single_nested)
    quam_dict["qubit"]["xy"]["mixer"] = {
        "id": 0,
        "port_I": 0,
        "port_Q": 1,
        "frequency_drive": 5e9,
        "local_oscillator": {"power": 10, "frequency": 6e9},
    }
    quam = QuamTestSingle.load(quam_dict)

    assert quam.qubit.xy.mixer.id == 0
    assert quam.qubit.xy.mixer.name == "mixer0"
    assert quam.qubit.xy.mixer.local_oscillator.power == 10
    assert quam.qubit.xy.mixer.local_oscillator.frequency == 6e9

    assert quam.qubit._quam is quam
    assert quam.qubit.xy._quam is quam
    assert quam.qubit.xy.mixer._quam is quam


def test_instantiate_wrong_type():
    class QuamTest(QuamBase):
        qubit: Transmon

    with pytest.raises(TypeError):
        QuamTest.load({"qubit": 0})


def test_instantiate_component_wrong_type():
    @dataclass
    class QuamTestComponent(QuamComponent):
        test_str: str

    instantiate_quam_component(QuamTestComponent, {"test_str": "hello"})

    with pytest.raises(TypeError):
        instantiate_quam_component(QuamTestComponent, {"test_str": 0})

    instantiate_quam_component(
        QuamTestComponent, {"test_str": 0}, validate_type=False
    )


def test_instantiate_quam_dict():
    @dataclass
    class QuamTest(QuamBase):
        qubit: Transmon
        wiring: dict


    quam_dict = deepcopy(quam_dict_single_nested)
    quam_dict["qubit"]["xy"]["mixer"] = {
        "id": 0,
        "port_I": ":wiring.port_I",
        "port_Q": ":wiring.port_Q",
        "frequency_drive": 5e9,
        "local_oscillator": {"power": 10, "frequency": 6e9},
    }
    quam_dict["wiring"] = {
        "port_I": 0,
        "port_Q": 1,
    }
    QuamTest.load(quam_dict)


def test_instantiation_fixed_attrs():
    @dataclass
    class TestComponent(QuamComponent):
        int_val: int

    quam_element = instantiate_quam_component(TestComponent, {"int_val": 42})
    assert quam_element.int_val == 42

    with pytest.raises(AttributeError):
        instantiate_quam_component(TestComponent, {"int_val": 42, "extra": 43})

    quam_element = instantiate_quam_component(
        TestComponent, {"int_val": 42, "extra": 43}, fix_attrs=False
    )
    assert quam_element.int_val == 42
    assert quam_element.extra == 43
