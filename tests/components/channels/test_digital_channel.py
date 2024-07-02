from copy import deepcopy
from quam.components import Channel, DigitalOutputChannel, pulses
from quam.components.ports.digital_outputs import OPXPlusDigitalOutputPort
from quam.core import QuamRoot, quam_dataclass
from quam.core.quam_instantiation import instantiate_quam_class


@quam_dataclass
class QuamTest(QuamRoot):
    channel: Channel


def test_digital_only_channel(qua_config):
    channel = Channel(
        id="channel",
        digital_outputs={"1": DigitalOutputChannel(opx_output=("con1", 1))},
    )

    quam = QuamTest(channel=channel)
    cfg = quam.generate_config()

    qua_config["controllers"] = {
        "con1": {"digital_outputs": {1: {"inverted": False, "shareable": False}}}
    }
    qua_config["elements"] = {
        "channel": {"digitalInputs": {"1": {"port": ("con1", 1)}}, "operations": {}}
    }

    assert cfg == qua_config


def test_digital_only_channel_with_port(qua_config):

    channel = Channel(
        id="channel",
        digital_outputs={
            "1": DigitalOutputChannel(
                opx_output=OPXPlusDigitalOutputPort(
                    "con1", 2, inverted=True, shareable=True
                )
            )
        },
    )

    quam = QuamTest(channel=channel)
    cfg = quam.generate_config()

    qua_config["controllers"] = {
        "con1": {"digital_outputs": {2: {"inverted": True, "shareable": True}}}
    }
    qua_config["elements"] = {
        "channel": {"digitalInputs": {"1": {"port": ("con1", 2)}}, "operations": {}}
    }

    assert cfg == qua_config


def test_digital_only_pulse(qua_config):
    channel = Channel(
        id="channel",
        operations={
            "digital": pulses.Pulse(length=100, digital_marker=[(1, 20, 0, 10)])
        },
        # digital_outputs={"1": DigitalOutputChannel(opx_output=("con1", 1))},
    )

    quam = QuamTest(channel=channel)
    cfg = quam.generate_config()

    qua_config["elements"] = {
        "channel": {"operations": {"digital": "channel.digital.pulse"}}
    }
    qua_config["pulses"]["channel.digital.pulse"] = {
        "length": 100,
        "operation": "control",
        "digital_marker": "channel.digital.dm",
    }
    qua_config["digital_waveforms"]["channel.digital.dm"] = {
        "samples": [(1, 20, 0, 10)]
    }

    assert cfg == qua_config


def test_instantiate_digital_channel():
    channel = instantiate_quam_class(
        quam_class=DigitalOutputChannel, contents={"opx_output": ["con1", 1]}
    )

    assert channel.opx_output == ("con1", 1)
