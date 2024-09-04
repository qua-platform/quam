from copy import deepcopy

import pytest
from quam.components.channels import IQChannel, InOutIQChannel, InOutSingleChannel

from quam.components.octave import Octave, OctaveUpConverter, OctaveDownConverter
from quam.core.quam_classes import QuamRoot, quam_dataclass


@quam_dataclass
class OctaveQuAM(QuamRoot):
    octave: Octave


@pytest.fixture
def octave():
    return Octave(name="octave1", ip="127.0.0.1", port=80)


def test_instantiate_octave(octave):
    assert octave.name == "octave1"
    assert octave.ip == "127.0.0.1"
    assert octave.port == 80
    assert octave.RF_outputs == {}
    assert octave.RF_inputs == {}
    assert octave.loopbacks == []


def test_empty_octave_config(octave, qua_config):
    machine = OctaveQuAM(octave=octave)
    config = machine.generate_config()

    qua_config["octaves"] = {
        "octave1": {
            "RF_outputs": {},
            "RF_inputs": {},
            "IF_outputs": {},
            "loopbacks": [],
        }
    }

    assert config == qua_config


def test_empty_octave_empty_config(octave):
    cfg = {}
    octave.apply_to_config(config=cfg)

    expected_cfg = {
        "octaves": {
            "octave1": {
                "RF_outputs": {},
                "RF_inputs": {},
                "IF_outputs": {},
                "loopbacks": [],
            }
        }
    }
    assert cfg == expected_cfg


def test_octave_config_conflicting_entry(octave):
    machine = OctaveQuAM(octave=octave)
    config = machine.generate_config()

    with pytest.raises(KeyError):
        octave.apply_to_config(config)


def test_get_octave_config(octave):
    octave_config = octave.get_octave_config()
    assert list(octave_config.devices) == ["octave1"]
    connection_details = octave_config.devices["octave1"]
    assert connection_details.host == "127.0.0.1"
    assert connection_details.port == 80


def test_frequency_converter_no_octave():
    converter = OctaveUpConverter(id=1, LO_frequency=2e9)
    assert converter.octave is None


def test_frequency_converter_octave(octave):
    converter = octave.RF_outputs[1] = OctaveUpConverter(id=1, LO_frequency=2e9)
    assert converter.octave is octave


def test_frequency_up_converter_apply_to_config(octave):
    converter = octave.RF_outputs[1] = OctaveUpConverter(id=1, LO_frequency=2e9)
    cfg = {}
    octave.apply_to_config(config=cfg)
    converter.apply_to_config(cfg)

    expected_cfg = {
        "octaves": {
            "octave1": {
                "RF_outputs": {
                    1: {
                        "LO_frequency": 2e9,
                        "LO_source": "internal",
                        "gain": 0,
                        "output_mode": "always_off",
                        "input_attenuators": "off",
                    }
                },
                "RF_inputs": {},
                "IF_outputs": {},
                "loopbacks": [],
            }
        }
    }
    assert cfg == expected_cfg


def test_frequency_down_converter_apply_to_config(octave):
    converter = octave.RF_inputs[1] = OctaveDownConverter(id=1, LO_frequency=2e9)
    cfg = {}
    octave.apply_to_config(config=cfg)
    converter.apply_to_config(cfg)

    expected_cfg = {
        "octaves": {
            "octave1": {
                "RF_outputs": {},
                "RF_inputs": {
                    1: {
                        "LO_frequency": 2e9,
                        "RF_source": "RF_in",
                        "LO_source": "internal",
                        "IF_mode_I": "direct",
                        "IF_mode_Q": "direct",
                    }
                },
                "IF_outputs": {},
                "loopbacks": [],
            }
        }
    }
    assert cfg == expected_cfg


def test_frequency_down_converter_with_IQchannel_apply_to_config(octave):
    channel = InOutIQChannel(
        opx_output_I=("con1", 3),
        opx_output_Q=("con1", 4),
        opx_input_I=("con1", 1),
        opx_input_Q=("con1", 2),
        frequency_converter_up=None,
        frequency_converter_down=None,
    )
    converter = octave.RF_inputs[1] = OctaveDownConverter(
        id=1, LO_frequency=2e9, channel=channel
    )
    cfg = {}
    octave.apply_to_config(config=cfg)
    converter.apply_to_config(cfg)

    expected_cfg = {
        "octaves": {
            "octave1": {
                "RF_outputs": {},
                "RF_inputs": {
                    1: {
                        "LO_frequency": 2e9,
                        "RF_source": "RF_in",
                        "LO_source": "internal",
                        "IF_mode_I": "direct",
                        "IF_mode_Q": "direct",
                    }
                },
                "IF_outputs": {
                    "IF_out1": {"port": ("con1", 1), "name": "out1"},
                    "IF_out2": {"port": ("con1", 2), "name": "out2"},
                },
                "loopbacks": [],
            }
        }
    }
    assert cfg == expected_cfg


def test_frequency_converter_down_existing_IF_outputs(octave):
    channel = InOutIQChannel(
        opx_output_I=("con1", 3),
        opx_output_Q=("con1", 4),
        opx_input_I=("con1", 2),
        opx_input_Q=("con1", 1),
        frequency_converter_up=None,
        frequency_converter_down=None,
    )
    converter = octave.RF_inputs[1] = OctaveDownConverter(
        id=1, LO_frequency=2e9, channel=channel
    )
    cfg = {}
    octave.apply_to_config(config=cfg)
    cfg["octaves"]["octave1"]["IF_outputs"] = {
        "IF_out1": {"port": ("con1", 1), "name": "out1"},
        "IF_out2": {"port": ("con1", 2), "name": "out2"},
    }

    with pytest.raises(ValueError):
        converter.apply_to_config(cfg)

    cfg = {}
    octave.apply_to_config(config=cfg)
    cfg["octaves"]["octave1"]["IF_outputs"] = {
        "IF_out1": {"port": ("con1", 2), "name": "out1"},
        "IF_out2": {"port": ("con1", 1), "name": "out2"},
    }

    converter.apply_to_config(cfg)

    assert cfg["octaves"]["octave1"]["IF_outputs"] == {
        "IF_out1": {"port": ("con1", 2), "name": "out1"},
        "IF_out2": {"port": ("con1", 1), "name": "out2"},
    }


def test_frequency_down_converter_with_single_channel_apply_to_config(octave):
    channel = InOutSingleChannel(
        opx_output=("con1", 3),
        opx_input=("con1", 3),
    )
    converter = octave.RF_inputs[1] = OctaveDownConverter(
        id=1, LO_frequency=2e9, channel=channel, IF_output_I=2
    )
    cfg = {}
    octave.apply_to_config(config=cfg)
    converter.apply_to_config(cfg)

    expected_cfg = {
        "octaves": {
            "octave1": {
                "RF_outputs": {},
                "RF_inputs": {
                    1: {
                        "LO_frequency": 2e9,
                        "RF_source": "RF_in",
                        "LO_source": "internal",
                        "IF_mode_I": "direct",
                        "IF_mode_Q": "direct",
                    }
                },
                "IF_outputs": {
                    "IF_out2": {"port": ("con1", 3), "name": "out1"},
                },
                "loopbacks": [],
            }
        }
    }
    assert cfg == expected_cfg


def test_instantiate_octave_default_connectivity(octave):
    octave.initialize_frequency_converters()

    assert list(octave.RF_outputs) == [1, 2, 3, 4, 5]
    for idx, RF_output in octave.RF_outputs.items():
        assert RF_output.octave == octave
        assert RF_output.id == idx

    assert list(octave.RF_inputs) == [1, 2]
    for idx, RF_input in octave.RF_inputs.items():
        assert RF_input.octave == octave
        assert RF_input.id == idx


def test_channel_add_RF_outputs(octave, qua_config):
    OctaveQuAM(octave=octave)
    octave.RF_outputs[2] = OctaveUpConverter(id=2, LO_frequency=2e9)

    channel = IQChannel(
        id="ch",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up="#/octave/RF_outputs/2",
    )

    channel.apply_to_config(qua_config)

    expected_cfg_elements = {
        "ch": {
            "RF_inputs": {"port": ("octave1", 2)},
            "operations": {},
        }
    }

    assert qua_config["elements"] == expected_cfg_elements


def test_channel_add_RF_inputs(octave, qua_config):
    OctaveQuAM(octave=octave)
    octave.RF_outputs[3] = OctaveUpConverter(id=3, LO_frequency=2e9)
    octave.RF_inputs[4] = OctaveDownConverter(id=4, LO_frequency=2e9)

    channel = InOutIQChannel(
        id="ch",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        opx_input_I=("con1", 1),
        opx_input_Q=("con1", 2),
        frequency_converter_up="#/octave/RF_outputs/3",
        frequency_converter_down="#/octave/RF_inputs/4",
    )

    channel.apply_to_config(qua_config)

    expected_cfg_elements = {
        "ch": {
            "RF_inputs": {"port": ("octave1", 3)},
            "RF_outputs": {"port": ("octave1", 4)},
            "operations": {},
            "smearing": 0,
            "time_of_flight": 24,
        }
    }

    assert qua_config["elements"] == expected_cfg_elements


def test_load_octave(octave):
    machine = OctaveQuAM(octave=octave)
    octave.initialize_frequency_converters()

    d = machine.to_dict()

    d_expected = {
        "__class__": "test_octave.OctaveQuAM",
        "octave": {
            "RF_inputs": {1: {"id": 1}, 2: {"id": 2, "LO_source": "external"}},
            "RF_outputs": {
                1: {"id": 1},
                2: {"id": 2},
                3: {"id": 3},
                4: {"id": 4},
                5: {"id": 5},
            },
            "ip": "127.0.0.1",
            "name": "octave1",
            "port": 80,
        },
    }
    assert d == d_expected

    machine2 = OctaveQuAM.load(d)

    assert d == machine2.to_dict()


def test_frequency_converter_config_no_LO_frequency(octave):
    cfg = {}
    converter = octave.RF_outputs[1] = OctaveUpConverter(id=1)
    octave.apply_to_config(config=cfg)

    converter.apply_to_config(cfg)

    expected_cfg = {
        "octaves": {
            "octave1": {
                "RF_outputs": {},
                "RF_inputs": {},
                "IF_outputs": {},
                "loopbacks": [],
            }
        }
    }
    assert cfg == expected_cfg

    converter.channel = "something"

    with pytest.raises(ValueError):
        converter.apply_to_config(cfg)

    converter.channel = None
    converter.LO_frequency = 2e9

    converter.apply_to_config(cfg)

    expected_cfg = {
        "octaves": {
            "octave1": {
                "IF_outputs": {},
                "RF_inputs": {},
                "RF_outputs": {
                    1: {
                        "LO_frequency": 2000000000.0,
                        "LO_source": "internal",
                        "gain": 0,
                        "input_attenuators": "off",
                        "output_mode": "always_off",
                    }
                },
                "loopbacks": [],
            }
        }
    }
    assert cfg == expected_cfg
