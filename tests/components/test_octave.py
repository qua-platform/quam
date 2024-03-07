from copy import deepcopy

import pytest
from quam.components.channels import InOutIQChannel, InOutSingleChannel

from quam.components.octave import Octave, OctaveUpConverter, OctaveDownConverter
from quam.core.qua_config_template import qua_config_template
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


def test_empty_octave_config(octave):
    machine = OctaveQuAM(octave=octave)
    config = machine.generate_config()

    expected_cfg = deepcopy(qua_config_template)
    expected_cfg["octaves"] = {
        "octave1": {
            "RF_outputs": {},
            "RF_inputs": {},
            "IF_outputs": {},
            "loopbacks": [],
        }
    }

    assert config == expected_cfg


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
                        "output_mode": "always_on",
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
    octave.initialize_default_connectivity()

    assert list(octave.RF_outputs) == [1, 2, 3, 4, 5]
    for idx, RF_output in octave.RF_outputs.items():
        assert RF_output.octave == octave
        assert RF_output.id == idx

    assert list(octave.RF_inputs) == [1, 2]
    for idx, RF_input in octave.RF_inputs.items():
        assert RF_input.octave == octave
        assert RF_input.id == idx
