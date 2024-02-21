import numpy as np
import pytest

from quam.core import *
from quam.components import *
from quam.components.channels import Channel, IQChannel, SingleChannel


def test_drag_pulse():
    drag_pulse = pulses.DragPulse(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20, axis_angle=0
    )

    assert drag_pulse.operation == "control"
    assert drag_pulse.length == 20
    assert drag_pulse.get_attrs() == {
        "id": None,
        "length": 20,
        "axis_angle": 0.0,
        "digital_marker": None,
        "amplitude": 1,
        "sigma": 4,
        "alpha": 2,
        "anharmonicity": 200000000.0,
        "detuning": 0.0,
        "subtracted": True,
    }

    waveform = drag_pulse.calculate_waveform()
    assert len(waveform) == 20
    assert isinstance(waveform, np.ndarray)
    assert np.iscomplexobj(waveform)


def test_channel():
    channel = Channel()
    d = channel.to_dict()

    assert d == {}


def test_IQ_channel():
    IQ_channel = IQChannel(
        opx_output_I=0,
        opx_output_Q=1,
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )
    d = IQ_channel.to_dict()
    assert d == {
        "opx_output_I": 0,
        "opx_output_Q": 1,
        "intermediate_frequency": 100e6,
        "frequency_converter_up": {"mixer": {}, "local_oscillator": {}},
    }


def test_single_pulse_IQ_channel():
    IQ_channel = IQChannel(
        id="IQ",
        opx_output_I=0,
        opx_output_Q=1,
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )
    IQ_channel.operations["X180"] = pulses.GaussianPulse(
        length=16, amplitude=1, sigma=12
    )

    cfg = {"pulses": {}, "waveforms": {}}
    pulse = IQ_channel.operations["X180"]

    with pytest.raises(ValueError) as exc_info:
        pulse.apply_to_config(cfg)
    error_message = "Waveform type 'single' not allowed for IQChannel 'IQ'"
    assert str(exc_info.value) == error_message

    pulse.axis_angle = 90
    pulse.apply_to_config(cfg)


def test_IQ_pulse_single_channel():
    single_channel = SingleChannel(
        id="single",
        opx_output=0,
    )
    single_channel.operations["X180"] = pulses.DragPulse(
        length=16,
        axis_angle=0,
        amplitude=1,
        sigma=12,
        alpha=0.1,
        anharmonicity=200e6,
    )

    cfg = {"pulses": {}, "waveforms": {}}
    pulse = single_channel.operations["X180"]

    with pytest.raises(ValueError) as exc_info:
        pulse.apply_to_config(cfg)
    error_message = "Waveform type 'IQ' not allowed for SingleChannel 'single'"
    assert str(exc_info.value) == error_message


def test_IQ_pulse_play_validate():
    single_channel = SingleChannel(
        id="single",
        opx_output=0,
    )

    with pytest.raises(KeyError):
        single_channel.play("X180")

    with pytest.raises(IndexError):
        single_channel.play("X180", validate=False)

    single_channel.operations["X180"] = pulses.DragPulse(
        length=16,
        axis_angle=0,
        amplitude=1,
        sigma=12,
        alpha=0.1,
        anharmonicity=200e6,
    )

    with pytest.raises(IndexError):
        single_channel.play("X180")


def test_pulse_parent_channel():
    pulse = pulses.SquarePulse(length=60, amplitude=0)
    assert pulse.parent is None
    assert pulse.channel is None

    channel = SingleChannel(id="single", opx_output=0)
    pulse.parent = channel
    assert pulse.parent is channel
    assert pulse.channel is channel


def test_pulse_parent_parent_channel():
    pulse = pulses.SquarePulse(length=60, amplitude=0)
    channel = SingleChannel(id="single", opx_output=0)
    channel.operations["pulse"] = pulse
    assert pulse.parent is channel.operations
    assert pulse.channel is channel
