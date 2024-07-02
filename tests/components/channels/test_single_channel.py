import pytest
import json
from copy import deepcopy

from quam.components import *
from quam.components.ports.analog_outputs import OPXPlusAnalogOutputPort
from quam.core import quam_dataclass, QuamRoot


@pytest.fixture
def bare_cfg():
    return {
        "controllers": {},
        "elements": {},
    }


def test_single_channel_no_name(bare_cfg):
    channel = SingleChannel(opx_output=("con1", 1))

    with pytest.raises(AttributeError):
        channel.apply_to_config(bare_cfg)

    channel.id = "channel"
    channel.apply_to_config(bare_cfg)


def test_single_channel_offset(bare_cfg):
    channel = SingleChannel(id="channel", opx_output=("con1", 1))

    cfg = deepcopy(bare_cfg)
    channel.apply_to_config(cfg)

    expected_cfg = {
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"delay": 0, "shareable": False}},
            }
        },
        "elements": {
            "channel": {
                "singleInput": {"port": ("con1", 1)},
                "operations": {},
            }
        },
    }
    assert cfg == expected_cfg

    cfg = deepcopy(bare_cfg)
    channel.opx_output_offset = 0.1
    expected_cfg["controllers"]["con1"]["analog_outputs"][1]["offset"] = 0.1
    channel.apply_to_config(cfg)
    assert cfg == expected_cfg


def test_single_channel_differing_offsets(bare_cfg):
    channel1 = SingleChannel(id="channel", opx_output=("con1", 1))
    channel2 = SingleChannel(id="channel2", opx_output=("con1", 1))

    cfg = deepcopy(bare_cfg)
    channel1.apply_to_config(cfg)
    channel2.apply_to_config(cfg)
    assert cfg["controllers"]["con1"]["analog_outputs"][1] == {
        "delay": 0,
        "shareable": False,
    }

    channel1.opx_output_offset = 0.1

    cfg = deepcopy(bare_cfg)
    channel1.apply_to_config(cfg)
    channel2.apply_to_config(cfg)
    assert cfg["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0.1

    channel2.opx_output_offset = 0.1

    cfg = deepcopy(bare_cfg)
    channel1.apply_to_config(cfg)
    channel2.apply_to_config(cfg)
    assert cfg["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0.1

    channel2.opx_output_offset = 0.2

    cfg = deepcopy(bare_cfg)
    channel1.apply_to_config(cfg)
    with pytest.warns(UserWarning):
        channel2.apply_to_config(cfg)

    cfg = deepcopy(bare_cfg)
    channel1.apply_to_config(cfg)
    channel2.opx_output_offset = 0.1 + 0.5e-4
    channel2.apply_to_config(cfg)
    assert cfg["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0.1 + 0.5e-4


def test_single_channel_offset_quam(qua_config):
    @quam_dataclass
    class QuamTest(QuamRoot):
        channel: SingleChannel

    channel = SingleChannel(id="channel", opx_output=("con1", 1))
    machine = QuamTest(channel=channel)

    cfg = machine.generate_config()

    qua_config["controllers"] = {
        "con1": {
            "analog_outputs": {1: {"delay": 0, "shareable": False, "offset": 0.0}},
        }
    }
    qua_config["elements"] = {
        "channel": {
            "singleInput": {"port": ("con1", 1)},
            "operations": {},
        }
    }

    assert cfg == qua_config

    channel.opx_output_offset = 0.1

    cfg = machine.generate_config()
    qua_config["controllers"]["con1"]["analog_outputs"][1]["offset"] = 0.1
    assert cfg == qua_config


def test_single_channel_set_dc_offset(mocker):
    mocker.patch("quam.components.channels.set_dc_offset")

    channel = SingleChannel(id="channel", opx_output=("con1", 1))
    channel.set_dc_offset(0.5)

    from quam.components.channels import set_dc_offset

    set_dc_offset.assert_called_once_with(
        element="channel", element_input="single", offset=0.5
    )


def test_instantiate_single_channel():
    from quam.core.quam_instantiation import instantiate_quam_class

    channel = SingleChannel(opx_output=("con1", 1))
    d = channel.to_dict()

    d_json = json.dumps(d)

    d_loaded = json.loads(d_json)

    instantiate_quam_class(SingleChannel, d_loaded)


def test_generate_config(qua_config):
    channel = SingleChannel(
        id="out_channel",
        opx_output=("con1", 1),
    )

    channel.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_outputs": {
                1: {"delay": 0, "shareable": False},
            },
        }
    }

    assert qua_config["elements"] == {
        "out_channel": {"operations": {}, "singleInput": {"port": ("con1", 1)}}
    }


def test_generate_config_port(qua_config):
    channel = SingleChannel(
        id="out_channel",
        opx_output=OPXPlusAnalogOutputPort("con1", 1),
    )

    channel.apply_to_config(qua_config)
    channel.opx_output.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_outputs": {
                1: {"delay": 0, "shareable": False},
            },
        }
    }

    assert qua_config["elements"] == {
        "out_channel": {"operations": {}, "singleInput": {"port": ("con1", 1)}}
    }
