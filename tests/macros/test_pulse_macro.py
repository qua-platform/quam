import pytest
from quam.components import Qubit
from quam.components.channels import IQChannel
from quam.components.pulses import SquarePulse
from quam.core.quam_classes import QuamRoot, quam_dataclass
from quam.components.macro import PulseMacro

try:
    from qm.exceptions import NoScopeFoundException
except ImportError:
    NoScopeFoundException = IndexError


@quam_dataclass
class MockQubit(Qubit):
    xy: IQChannel


@quam_dataclass
class Quam(QuamRoot):
    qubit: MockQubit


@pytest.fixture
def test_qubit():
    return MockQubit(
        id=0,
        xy=IQChannel(
            opx_output_I=("con1", 1),
            opx_output_Q=("con1", 2),
            frequency_converter_up=None,
            operations={"test_pulse": SquarePulse(length=100, amplitude=1.0)},
        ),
    )


def test_pulse_macro_no_pulse(test_qubit):
    with pytest.raises(
        (TypeError, ValueError),
        match=r"(missing 1 required keyword-only argument: 'pulse'|Please provide PulseMacro.pulse as it is a required arg)",
    ):
        PulseMacro()


def test_pulse_macro_pulse_string(test_qubit, mocker):
    pulse_macro = PulseMacro(pulse="test_pulse")
    assert pulse_macro.pulse == "test_pulse"

    with pytest.raises(AttributeError):
        pulse_macro.qubit

    test_qubit.macros["test_pulse"] = pulse_macro

    assert pulse_macro.qubit is test_qubit

    assert test_qubit.get_macros() == {
        "test_pulse": pulse_macro,
        "align": test_qubit.align,
    }

    with pytest.raises(NoScopeFoundException):
        test_qubit.apply("test_pulse")

    mocker.patch("quam.components.channels.play")

    test_qubit.apply("test_pulse")

    from quam.components.channels import play

    play.assert_called_once()


def test_pulse_macro_pulse_object_error(test_qubit):
    pulse_macro = PulseMacro(
        pulse=SquarePulse(id="test_pulse", length=100, amplitude=1.0)
    )
    test_qubit.macros["pulse_macro"] = pulse_macro
    with pytest.raises(
        ValueError, match="Pulse 'test_pulse' is not attached to a channel"
    ):
        test_qubit.apply("pulse_macro")


def test_pulse_macro_pulse_reference(test_qubit, mocker):
    machine = Quam(qubit=test_qubit)  # Need root to get pulse reference

    pulse_macro = PulseMacro(
        pulse=test_qubit.xy.operations["test_pulse"].get_reference()
    )
    assert pulse_macro.pulse == test_qubit.xy.operations["test_pulse"]

    test_qubit.macros["pulse_macro"] = pulse_macro

    mocker.patch("quam.components.channels.play")

    test_qubit.apply("pulse_macro")

    from quam.components.channels import play

    play.assert_called_once()
