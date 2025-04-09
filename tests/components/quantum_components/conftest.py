from typing import Dict, Optional
import pytest
from quam.components import Qubit, QubitPair
from quam.components.channels import IQChannel
from quam.core.quam_classes import QuamRoot, quam_dataclass
from dataclasses import field


@quam_dataclass
class MockQubit(Qubit):
    xy: IQChannel
    resonator: Optional[IQChannel] = None


@quam_dataclass
class TestQuam(QuamRoot):
    qubits: Dict[str, MockQubit] = field(default_factory=dict)
    qubit_pairs: Dict[str, QubitPair] = field(default_factory=dict)


@pytest.fixture
def mock_qubit():
    """Basic mock qubit with xy channel"""
    return MockQubit(
        id="q0",
        xy=IQChannel(
            opx_output_I=("con1", 1),
            opx_output_Q=("con1", 2),
            frequency_converter_up=None,
        ),
    )


@pytest.fixture
def mock_qubit_with_resonator():
    """Mock qubit with both xy and resonator channels"""
    return MockQubit(
        id="q1",
        xy=IQChannel(
            opx_output_I=("con1", 1),
            opx_output_Q=("con1", 2),
            frequency_converter_up=None,
        ),
        resonator=IQChannel(
            opx_output_I=("con1", 3),
            opx_output_Q=("con1", 4),
            frequency_converter_up=None,
        ),
    )


@pytest.fixture
def test_quam(mock_qubit, mock_qubit_with_resonator):
    """Test QUAM instance with qubits and qubit pairs"""
    machine = TestQuam(
        qubits={"q0": mock_qubit, "q1": mock_qubit_with_resonator},
    )
    machine.qubit_pairs["pair_0"] = QubitPair(
        qubit_control=mock_qubit.get_reference(),
        qubit_target=mock_qubit_with_resonator.get_reference(),
    )
    return machine
