from collections import UserDict
from dataclasses import field
from typing import Dict, List
import pytest
from quam.components import Qubit, QubitPair
from quam.components.channels import IQChannel
from quam.core.quam_classes import QuamRoot, quam_dataclass


@quam_dataclass
class MockQubit(Qubit):
    xy: IQChannel = None


@quam_dataclass
class MockQubitPair(QubitPair):
    qubit_control: MockQubit
    qubit_target: MockQubit


@quam_dataclass
class Quam(QuamRoot):
    qubits: Dict[str, MockQubit]
    qubit_pairs: Dict[str, MockQubitPair] = field(default_factory=dict)


@pytest.fixture
def test_qubit_control():
    return MockQubit(
        id="q1",
        xy=IQChannel(
            id="xy_control",
            opx_output_I=("con1", 1),
            opx_output_Q=("con1", 2),
            frequency_converter_up=None,
        ),
    )


@pytest.fixture
def test_qubit_target():
    return MockQubit(
        id="q2",
        xy=IQChannel(
            id="xy_target",
            opx_output_I=("con1", 5),
            opx_output_Q=("con1", 6),
            frequency_converter_up=None,
        ),
    )


@pytest.fixture
def test_quam(test_qubit_control, test_qubit_target):
    machine = Quam(
        qubits={"control": test_qubit_control, "target": test_qubit_target},
    )

    machine.qubit_pairs["pair_1"] = MockQubitPair(
        id="pair_1",
        qubit_control=test_qubit_control.get_reference(),
        qubit_target=test_qubit_target.get_reference(),
    )
    return machine


@pytest.fixture
def test_qubit_pair(test_quam):
    return test_quam.qubit_pairs["pair_1"]


def test_qubit_pair_initialization(
    test_qubit_pair, test_qubit_control, test_qubit_target
):
    """Test that QubitPair is initialized correctly"""
    assert test_qubit_pair.qubit_control == test_qubit_control
    assert test_qubit_pair.qubit_target == test_qubit_target
    assert test_qubit_pair.name == "pair_1"
    assert isinstance(test_qubit_pair.macros, UserDict)
    assert len(test_qubit_pair.macros) == 0


def test_qubit_pair_align(test_qubit_pair, mocker):
    """Test that align method calls the control qubit's align method with correct args"""
    mock_align = mocker.patch.object(test_qubit_pair.qubit_control, "align")

    test_qubit_pair.align()

    mock_align.assert_called_once_with(test_qubit_pair.qubit_target)


def test_qubit_pair_via_matmul(test_quam):
    """Test that qubit pair can be accessed via @ operator"""
    control = test_quam.qubits["control"]
    target = test_quam.qubits["target"]

    qubit_pair = control @ target

    assert isinstance(qubit_pair, QubitPair)
    assert qubit_pair.qubit_control == control
    assert qubit_pair.qubit_target == target


def test_matmul_with_invalid_qubit(test_quam):
    """Test that @ operator raises error for invalid qubit pairs"""
    control = test_quam.qubits["control"]

    with pytest.raises(ValueError, match="Cannot create a qubit pair with same qubit"):
        _ = control @ control

    with pytest.raises(
        ValueError, match="Cannot create a qubit pair .* with a non-qubit object"
    ):
        _ = control @ "not_a_qubit"


def test_matmul_with_nonexistent_pair(test_quam):
    """Test that @ operator raises error for non-existent qubit pairs"""
    target = test_quam.qubits["target"]
    control = test_quam.qubits["control"]

    # Try to access pair in reverse order (target @ control) when only (control @ target) exists
    with pytest.raises(ValueError, match="Qubit pair not found"):
        _ = target @ control
