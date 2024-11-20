from quam.components.channels import SingleChannel, TimeTaggingAddon
from quam.core.quam_classes import QuamRoot, quam_dataclass


@quam_dataclass
class SingleChannelQuAM(QuamRoot):
    channel: SingleChannel


def test_time_tagging_cfg():
    channel = SingleChannel(id="channel", opx_output=("con1", 1))
    channel.time_tagging = TimeTaggingAddon()

    machine = SingleChannelQuAM(channel=channel)
    cfg = machine.generate_config()

    assert "outputPulseParameters" in cfg["elements"]["channel"]
    assert cfg["elements"]["channel"]["outputPulseParameters"] == {
        "signalThreshold": 800,
        "signalPolarity": "below",
        "derivativeThreshold": 300,
        "derivativePolarity": "below",
    }


def test_time_tagging_cfg_disabled():
    channel = SingleChannel(id="channel", opx_output=("con1", 1))
    channel.time_tagging = TimeTaggingAddon(enabled=False)

    machine = SingleChannelQuAM(channel=channel)
    cfg = machine.generate_config()
    assert "outputPulseParameters" not in cfg["elements"]["channel"]


def test_time_tagging_cfg_custom_thresholds():
    channel = SingleChannel(id="channel", opx_output=("con1", 1))
    channel.time_tagging = TimeTaggingAddon(
        signal_threshold=0.2, derivative_threshold=0.1
    )

    machine = SingleChannelQuAM(channel=channel)
    cfg = machine.generate_config()
    assert "outputPulseParameters" in cfg["elements"]["channel"]
    assert cfg["elements"]["channel"]["outputPulseParameters"] == {
        "signalThreshold": int(0.2 * 4096),
        "signalPolarity": "below",
        "derivativeThreshold": int(0.1 * 4096),
        "derivativePolarity": "below",
    }