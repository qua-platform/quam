from typing import Optional
import pytest
from quam.components import Qubit
from quam.components.channels import IQChannel
from quam.components.pulses import SquarePulse
from quam.core.quam_classes import QuamRoot, quam_dataclass


def test_qubit_name_int():
    qubit = Qubit(id=0)
    assert qubit.name == "q0"


def test_qubit_name_str():
    qubit = Qubit(id="qubit0")
    assert qubit.name == "qubit0"


def test_qubit_channels(mock_qubit_with_resonator):
    assert mock_qubit_with_resonator.channels == {
        "xy": mock_qubit_with_resonator.xy,
        "resonator": mock_qubit_with_resonator.resonator,
    }


def test_qubit_channels_referenced(mock_qubit):
    # Set resonator as a reference to xy channel
    mock_qubit.resonator = "#./xy"

    assert mock_qubit.channels == {
        "xy": mock_qubit.xy,
        "resonator": mock_qubit.xy,
    }


def test_qubit_get_pulse_not_found(mock_qubit):
    with pytest.raises(ValueError, match="Pulse test_pulse not found"):
        mock_qubit.get_pulse("test_pulse")


def test_qubit_get_pulse_not_unique(mock_qubit_with_resonator):
    mock_qubit_with_resonator.xy.operations["test_pulse"] = SquarePulse(
        length=100, amplitude=1.0
    )
    mock_qubit_with_resonator.resonator.operations["test_pulse"] = SquarePulse(
        length=100, amplitude=1.0
    )

    with pytest.raises(ValueError, match="Pulse test_pulse is not unique"):
        mock_qubit_with_resonator.get_pulse("test_pulse")


def test_qubit_get_pulse_unique(mock_qubit):
    pulse = SquarePulse(length=100, amplitude=1.0)
    mock_qubit.xy.operations["test_pulse"] = pulse

    assert mock_qubit.get_pulse("test_pulse") == pulse


def test_qubit_align(mock_qubit_with_resonator, mock_qubit, mocker):
    mocker.patch("quam.components.quantum_components.qubit.align")
    mock_qubit_with_resonator.align(mock_qubit)

    from quam.components.quantum_components.qubit import align

    align.assert_called_once()
    called_args, _ = align.call_args
    assert set(called_args) == {"q1.xy", "q1.resonator", "q0.xy"}


def test_qubit_get_macros(mock_qubit):
    assert mock_qubit.macros == {}
    assert mock_qubit.get_macros() == {"align": mock_qubit.align}


def test_qubit_apply_align(mock_qubit_with_resonator, mocker):
    mocker.patch("quam.components.quantum_components.qubit.align")
    mock_qubit_with_resonator.align()

    from quam.components.quantum_components.qubit import align

    align.assert_called_once()
    called_args, _ = align.call_args
    assert set(called_args) == {"q1.xy", "q1.resonator"}


def test_qubit_inferred_id_direct():
    """Test inferred_id when id is a direct value"""
    qubit = Qubit(id=0)
    assert qubit.inferred_id == 0


def test_qubit_inferred_id_with_parent(test_quam):
    """Test inferred_id when id is a reference and qubit has parent"""
    test_quam.qubits["q2"] = Qubit()
    assert test_quam.qubits["q2"].inferred_id == "q2"


def test_qubit_inferred_id_no_parent():
    """Test inferred_id when id is a reference but qubit has no parent"""
    qubit = Qubit(id="#./inferred_id")
    with pytest.raises(
        AttributeError, match="Cannot infer id .* not attached to a parent"
    ):
        _ = qubit.inferred_id
