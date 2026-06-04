import pytest
from quam.components.channels import (
    SingleChannel,
    InSingleChannel,
    StickyChannelAddon,
    TimeTaggingAddon,
    DigitalOutputChannel,
)
from quam.components.ports.digital_outputs import FEMDigitalOutputPort
from quam.components.pulses import SquarePulse

from .conftest import make_lf_input_port, make_lf_output_port


def _add_sticky_single_channel(machine) -> None:
    machine.channels["drive"] = SingleChannel(
        opx_output=make_lf_output_port(1),
        sticky=StickyChannelAddon(duration=20, digital=False),
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


def _add_time_tagging_in_single_channel(machine) -> None:
    machine.channels["readout"] = InSingleChannel(
        opx_input=make_lf_input_port(1),
        time_of_flight=280,
        time_tagging=TimeTaggingAddon(),
    )


def _add_single_channel_with_digital_output(machine) -> None:
    machine.channels["drive"] = SingleChannel(
        opx_output=make_lf_output_port(1),
        digital_outputs={"trigger": DigitalOutputChannel(
            opx_output=FEMDigitalOutputPort("con1", 1, 1),
            delay=0,
            buffer=0,
        )},
        operations={"const": SquarePulse(length=1000, amplitude=0.1)},
    )


@pytest.mark.parametrize(
    "add_channel",
    [
        _add_sticky_single_channel,
        _add_time_tagging_in_single_channel,
        _add_single_channel_with_digital_output,
    ],
    ids=[
        "sticky_channel_addon",
        "time_tagging_addon",
        "digital_output_channel",
    ],
)
def test_channel_addon_config_is_valid(validate_quam_config, add_channel):
    validate_quam_config(add_channel)
