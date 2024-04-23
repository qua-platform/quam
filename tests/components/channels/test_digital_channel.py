from copy import deepcopy
from quam.components import Channel, DigitalOutputChannel, pulses
from quam.core import QuamRoot, quam_dataclass
from quam.core.qua_config_template import qua_config_template
from quam.core.quam_instantiation import instantiate_quam_class


@quam_dataclass
class QuamTest(QuamRoot):
    channel: Channel


def test_digital_only_channel():
    channel = Channel(
        id="channel",
        digital_outputs={"1": DigitalOutputChannel(opx_output=("con1", 1))},
    )

    quam = QuamTest(channel=channel)
    cfg = quam.generate_config()

    expected_cfg = deepcopy(qua_config_template)
    expected_cfg["controllers"] = {"con1": {"digital_outputs": {1: {}}}}
    expected_cfg["elements"] = {
        "channel": {"digitalInputs": {"1": {"port": ("con1", 1)}}, "operations": {}}
    }

    assert cfg == expected_cfg


def test_digital_only_pulse():
    channel = Channel(
        id="channel",
        operations={
            "digital": pulses.Pulse(length=100, digital_marker=[(1, 20, 0, 10)])
        },
        # digital_outputs={"1": DigitalOutputChannel(opx_output=("con1", 1))},
    )

    quam = QuamTest(channel=channel)
    cfg = quam.generate_config()

    expected_cfg = deepcopy(qua_config_template)
    # expected_cfg["controllers"] = {"con1": {"digital_outputs": {1: {}}}}
    expected_cfg["elements"] = {
        "channel": {"operations": {"digital": "channel.digital.pulse"}}
    }
    expected_cfg["pulses"]["channel.digital.pulse"] = {
        "length": 100,
        "operation": "control",
        "digital_marker": "channel.digital.dm",
    }
    expected_cfg["digital_waveforms"]["channel.digital.dm"] = {
        "samples": [(1, 20, 0, 10)]
    }

    assert cfg == expected_cfg


def test_instantiate_digital_channel():
    channel = instantiate_quam_class(
        quam_class=DigitalOutputChannel, contents={"opx_output": ["con1", 1]}
    )

    assert channel.opx_output == ("con1", 1)
