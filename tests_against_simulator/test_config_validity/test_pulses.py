import pytest
from quam.components.channels import IQChannel, InOutSingleChannel, SingleChannel
from quam.components.hardware import FrequencyConverter, LocalOscillator, Mixer
from quam.components.ports import LFFEMAnalogOutputPort, LFFEMAnalogInputPort
from quam.components.pulses import (
    DragCosinePulse,
    DragGaussianPulse,
    GaussianPulse,
    SquarePulse,
    SquareReadoutPulse,
    WaveformPulse,
)


def _iq_channel(operations):
    return IQChannel(
        opx_output_I=LFFEMAnalogOutputPort("con1", 1, 1),
        opx_output_Q=LFFEMAnalogOutputPort("con1", 1, 2),
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(),
            local_oscillator=LocalOscillator(frequency=5e9),
        ),
        intermediate_frequency=100e6,
        operations=operations,
    )


def _add_gaussian_pulse(machine) -> None:
    machine.channels["drive"] = SingleChannel(
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1),
        operations={"gaussian": GaussianPulse(amplitude=0.1, length=100, sigma=10.0)},
    )


def _add_square_pulse_with_axis_angle(machine) -> None:
    machine.channels["drive"] = _iq_channel({
        "Y90": SquarePulse(length=100, amplitude=0.1, axis_angle=0.5 * 3.14159),
    })


def _add_drag_gaussian_pulse(machine) -> None:
    machine.channels["drive"] = _iq_channel({
        "X90": DragGaussianPulse(
            length=100,
            axis_angle=0.0,
            amplitude=0.1,
            sigma=10.0,
            alpha=0.2,
            anharmonicity=-200e6,
        )
    })


def _add_drag_cosine_pulse(machine) -> None:
    machine.channels["drive"] = _iq_channel({
        "X90": DragCosinePulse(
            length=100,
            axis_angle=0.0,
            amplitude=0.1,
            alpha=0.2,
            anharmonicity=-200e6,
        )
    })


def _add_waveform_pulse(machine) -> None:
    machine.channels["drive"] = SingleChannel(
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1),
        operations={"arb": WaveformPulse(waveform_I=[0.1] * 100)},
    )


def _add_square_readout_pulse(machine) -> None:
    machine.channels["readout"] = InOutSingleChannel(
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1),
        opx_input=LFFEMAnalogInputPort("con1", 1, 2),
        time_of_flight=280,
        operations={"readout": SquareReadoutPulse(length=1000, amplitude=0.1)},
    )


@pytest.mark.parametrize(
    "add_channel",
    [
        _add_gaussian_pulse,
        _add_square_pulse_with_axis_angle,
        _add_drag_gaussian_pulse,
        _add_drag_cosine_pulse,
        _add_waveform_pulse,
        _add_square_readout_pulse,
    ],
    ids=[
        "gaussian_pulse",
        "square_pulse_axis_angle",
        "drag_gaussian_pulse",
        "drag_cosine_pulse",
        "waveform_pulse",
        "square_readout_pulse",
    ],
)
def test_pulse_config_is_valid(validate_quam_config, add_channel):
    validate_quam_config(add_channel)
