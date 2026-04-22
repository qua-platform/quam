import numpy as np
import pytest

from quam.core import *
from quam.components import *
from quam.components.channels import Channel, IQChannel, SingleChannel
from quam.utils.dataclass import get_dataclass_attr_annotations


@quam_dataclass
class QuAMTestPulseReferenced(QuamRoot):
    channel: SingleChannel


def test_pulses_referenced():

    channel = SingleChannel(id="single", opx_output=("con1", 1))
    machine = QuAMTestPulseReferenced(channel=channel)

    pulse = pulses.SquarePulse(length=60, amplitude=0)
    channel.operations["pulse"] = pulse
    channel.operations["pulse_referenced"] = "#./pulse"

    assert (
        channel.operations["pulse_referenced"] == channel.operations["pulse"] == pulse
    )

    state = machine.to_dict()

    machine_loaded = QuAMTestPulseReferenced.load(state)

    pulse_loaded = machine_loaded.channel.operations["pulse"]
    assert isinstance(pulse_loaded, pulses.SquarePulse)
    assert pulse_loaded.to_dict() == pulse.to_dict()

    assert machine_loaded.channel.operations["pulse_referenced"] == pulse_loaded
    assert (
        machine_loaded.channel.operations.get_unreferenced_value("pulse_referenced")
        == "#./pulse"
    )


def test_pulse_attr_annotations():
    from quam.components import pulses

    attr_annotations = get_dataclass_attr_annotations(pulses.SquareReadoutPulse)

    assert list(attr_annotations["required"]) == ["length", "amplitude"]


def test_cosinebipolarpulse():
    pulse = pulses._CosineBipolarPulse(
        amplitude=1.0, flat_length=80, smoothing_length=20, post_zero_padding_length=10
    )
    assert pulse.length == np.ceil((80 + 20 + 10) / 4) * 4
    assert pulse.amplitude == 1.0
    assert pulse.flat_length == 80
    assert pulse.axis_angle is None

    waveform = np.array(pulse.waveform_function())
    assert len(waveform) == np.ceil((80 + 20 + 10) / 4) * 4
    assert np.isclose(np.sum(waveform.real), 0, atol=1e-10)


def test_flattopgaussianpulse():
    pulse = pulses._FlatTopGaussianPulse(
        amplitude=1.0, flat_length=80, smoothing_length=20, post_zero_padding_length=10
    )
    assert pulse.length == np.ceil((80 + 20 + 10) / 4) * 4
    assert pulse.amplitude == 1.0
    assert pulse.flat_length == 80
    assert pulse.axis_angle is None

    waveform = np.array(pulse.waveform_function())
    assert len(waveform) == np.ceil((80 + 20 + 10) / 4) * 4
