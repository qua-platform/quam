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
