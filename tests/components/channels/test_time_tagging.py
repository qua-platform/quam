from quam.components.channels import InSingleChannel, TimeTaggingAddon
from quam.core.quam_classes import QuamRoot, quam_dataclass


@quam_dataclass
class SingleChannelQuam(QuamRoot):
    channel: InSingleChannel


def test_time_tagging_cfg():
    channel = InSingleChannel(id="channel", opx_input=("con1", 1))
    channel.time_tagging = TimeTaggingAddon()

    machine = SingleChannelQuam(channel=channel)
    cfg = machine.generate_config()

    assert "outputPulseParameters" in cfg["elements"]["channel"]
    assert cfg["elements"]["channel"]["outputPulseParameters"] == {
        "signalThreshold": 800,
        "signalPolarity": "below",
        "derivativeThreshold": 300,
        "derivativePolarity": "below",
    }


def test_time_tagging_cfg_disabled():
    channel = InSingleChannel(id="channel", opx_input=("con1", 1))
    channel.time_tagging = TimeTaggingAddon(enabled=False)

    machine = SingleChannelQuam(channel=channel)
    cfg = machine.generate_config()
    assert "outputPulseParameters" not in cfg["elements"]["channel"]


def test_time_tagging_cfg_custom_thresholds():
    channel = InSingleChannel(id="channel", opx_input=("con1", 1))
    channel.time_tagging = TimeTaggingAddon(
        signal_threshold=0.2, derivative_threshold=0.1
    )

    machine = SingleChannelQuam(channel=channel)
    cfg = machine.generate_config()
    assert "outputPulseParameters" in cfg["elements"]["channel"]
    assert cfg["elements"]["channel"]["outputPulseParameters"] == {
        "signalThreshold": int(0.2 * 4096),
        "signalPolarity": "below",
        "derivativeThreshold": int(0.1 * 4096),
        "derivativePolarity": "below",
    }
