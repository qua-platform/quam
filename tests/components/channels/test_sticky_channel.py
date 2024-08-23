import pytest
from quam.components.channels import IQChannel, StickyChannelAddon
from quam.core.quam_classes import QuamRoot, quam_dataclass


def test_sticky_channel_no_duration_error():
    with pytest.raises(TypeError):
        StickyChannelAddon()

    StickyChannelAddon(duration=20)


@quam_dataclass
class SingleChannelQuAM(QuamRoot):
    channel: IQChannel


def test_sticky_channel():
    channel = IQChannel(
        id="channel",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=None,
        sticky=StickyChannelAddon(duration=20),
    )
    machine = SingleChannelQuAM(channel=channel)

    cfg = machine.generate_config()

    channel_cfg = cfg["elements"]["channel"]
    assert "sticky" in channel_cfg
    assert channel_cfg["sticky"] == {
        "duration": 20,
        "analog": True,
        "digital": True,
    }


def test_sticky_channel_disabled():
    channel = IQChannel(
        id="channel",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=None,
        sticky=StickyChannelAddon(duration=20, enabled=False),
    )
    machine = SingleChannelQuAM(channel=channel)

    cfg = machine.generate_config()

    channel_cfg = cfg["elements"]["channel"]
    assert "sticky" not in channel_cfg
