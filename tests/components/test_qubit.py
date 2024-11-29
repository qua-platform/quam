import pytest
from quam.components import Qubit
from quam.components.channels import IQChannel
from quam.components.pulses import SquarePulse
from quam.core.quam_classes import quam_dataclass


def test_qubit_name_int():
    qubit = Qubit(id=0)
    assert qubit.name == "q0"


def test_qubit_name_str():
    qubit = Qubit(id="qubit0")
    assert qubit.name == "qubit0"


@quam_dataclass
class TestQubit(Qubit):
    xy: IQChannel
    resonator: IQChannel


@pytest.fixture
def test_qubit():
    return TestQubit(
        id=0,
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


def test_qubit_channels(test_qubit):
    assert test_qubit.channels == {
        "xy": test_qubit.xy,
        "resonator": test_qubit.resonator,
    }


@pytest.fixture
def test_qubit_referenced():
    return TestQubit(
        id=0,
        xy=IQChannel(
            opx_output_I=("con1", 1),
            opx_output_Q=("con1", 2),
            frequency_converter_up=None,
        ),
        resonator="#./xy",
    )


def test_qubit_channels_referenced(test_qubit_referenced):
    assert test_qubit_referenced.channels == {
        "xy": test_qubit_referenced.xy,
        "resonator": test_qubit_referenced.xy,
    }


def test_qubit_get_pulse_not_found(test_qubit):
    with pytest.raises(ValueError, match="Pulse test_pulse not found"):
        test_qubit.get_pulse("test_pulse")


def test_qubit_get_pulse_not_unique(test_qubit):
    test_qubit.xy.operations["test_pulse"] = SquarePulse(length=100, amplitude=1.0)
    test_qubit.resonator.operations["test_pulse"] = SquarePulse(
        length=100, amplitude=1.0
    )

    with pytest.raises(ValueError, match="Pulse test_pulse is not unique"):
        test_qubit.get_pulse("test_pulse")


def test_qubit_get_pulse_unique(test_qubit):
    pulse = SquarePulse(length=100, amplitude=1.0)
    test_qubit.xy.operations["test_pulse"] = pulse

    assert test_qubit.get_pulse("test_pulse") == pulse


def test_qubit_align(test_qubit, mocker):
    mocker.patch("quam.components.quantum_components.qubit.align")
    test_qubit.align(test_qubit)

    from quam.components.quantum_components.qubit import align

    align.assert_called_once_with("q0.xy", "q0.resonator")


def test_qubit_get_macros(test_qubit):
    assert test_qubit.macros == {}
    assert test_qubit.get_macros() == {"align": test_qubit.align}


def test_qubit_apply_align(test_qubit, mocker):
    mocker.patch("quam.components.quantum_components.qubit.align")
    test_qubit.apply("align")

    from quam.components.quantum_components.qubit import align

    align.assert_called_once_with("q0.xy", "q0.resonator")
