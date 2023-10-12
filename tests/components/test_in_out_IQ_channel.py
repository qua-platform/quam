import pytest
from quam.components import *


def test_empty_in_out_IQ_channel():
    readout_resonator = InOutIQChannel(
        mixer=Mixer(),
        output_port_I=("con1", 1),
        output_port_Q=("con1", 2),
        input_port_I=("con1", 3),
        input_port_Q=("con1", 4),
        intermediate_frequency=100e6,
        local_oscillator=LocalOscillator(frequency=5e9),
    )

    mixer = readout_resonator.mixer
    assert mixer.local_oscillator_frequency == 5e9
    assert mixer.intermediate_frequency == 100e6
    assert mixer.offset_I == 0
    assert mixer.offset_Q == 0

    with pytest.raises(AttributeError):
        mixer.name
    assert readout_resonator.id == ":../id"  # parent not defined
    with pytest.raises(AttributeError):
        readout_resonator.name

    readout_resonator.id = 1

    d = readout_resonator.to_dict()
    assert d == {
        "mixer": {},
        "output_port_I": ("con1", 1),
        "output_port_Q": ("con1", 2),
        "input_port_I": ("con1", 3),
        "input_port_Q": ("con1", 4),
        "intermediate_frequency": 100000000.0,
        "local_oscillator": {"frequency": 5000000000.0},
        "id": 1,
    }

    cfg = {
        "controllers": {},
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
    }
    expected_cfg = {
        "controllers": {
            "con1": {
                "analog_inputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                },
                "analog_outputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                },
                "digital_outputs": {},
            }
        },
        "elements": {
            "r1": {
                "intermediate_frequency": 100000000.0,
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "r1$mixer",
                },
                "operations": {},
                "outputs": {"out1": ("con1", 3), "out2": ("con1", 4)},
                "smearing": 0,
                "time_of_flight": 24,
            }
        },
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
    }
    readout_resonator.apply_to_config(cfg)
    assert cfg == expected_cfg


def test_readout_resonator_with_readout():
    readout_resonator = InOutIQChannel(
        id=1,
        mixer=Mixer(),
        output_port_I=("con1", 1),
        output_port_Q=("con1", 2),
        input_port_I=("con1", 3),
        input_port_Q=("con1", 4),
        intermediate_frequency=100e6,
        local_oscillator=LocalOscillator(frequency=5e9),
    )
    readout_resonator.operations["readout"] = pulses.ConstantReadoutPulse(
        amplitude=0.1, length=1000
    )

    d = readout_resonator.to_dict()
    assert d == {
        "mixer": {},
        "output_port_I": ("con1", 1),
        "output_port_Q": ("con1", 2),
        "input_port_I": ("con1", 3),
        "input_port_Q": ("con1", 4),
        "intermediate_frequency": 100000000.0,
        "local_oscillator": {"frequency": 5000000000.0},
        "id": 1,
        "operations": {
            "readout": {
                "__class__": "quam.components.pulses.ConstantReadoutPulse",
                "amplitude": 0.1,
                "length": 1000,
            }
        },
    }

    cfg = {
        "controllers": {},
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
        "digital_waveforms": {},
    }
    expected_cfg = {
        "controllers": {
            "con1": {
                "analog_inputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                },
                "analog_outputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                },
                "digital_outputs": {},
            }
        },
        "elements": {
            "r1": {
                "intermediate_frequency": 100000000.0,
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "r1$mixer",
                },
                "outputs": {"out1": ("con1", 3), "out2": ("con1", 4)},
                "smearing": 0,
                "time_of_flight": 24,
                "operations": {"readout": "r1$readout$pulse"},
            }
        },
        "pulses": {},
        "integration_weights": {},
        "waveforms": {},
        "digital_waveforms": {},
    }
    readout_resonator.apply_to_config(cfg)
    assert cfg == expected_cfg

    cfg = {
        "controllers": {},
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
        "digital_waveforms": {},
    }

    with pytest.raises(KeyError):
        readout_resonator.operations["readout"].apply_to_config(cfg)

    cfg["digital_waveforms"]["ON"] = {"samples": [(1, 0)]}
    readout_resonator.operations["readout"].apply_to_config(cfg)
    expected_cfg = {
        "controllers": {},
        "digital_waveforms": {"ON": {"samples": [(1, 0)]}},
        "elements": {},
        "integration_weights": {
            "r1$readout$iw1": {"cosine": [(1.0, 1000)], "sine": [(-0.0, 1000)]},
            "r1$readout$iw2": {"cosine": [(0.0, 1000)], "sine": [(1.0, 1000)]},
            "r1$readout$iw3": {"cosine": [(-0.0, 1000)], "sine": [(-1.0, 1000)]},
        },
        "pulses": {
            "r1$readout$pulse": {
                "digital_marker": "ON",
                "integration_weights": {
                    "iw1": "r1$readout$iw1",
                    "iw2": "r1$readout$iw2",
                    "iw3": "r1$readout$iw3",
                },
                "length": 1000,
                "operation": "measurement",
                "waveforms": {"I": "r1$readout$wf$I", "Q": "r1$readout$wf$Q"},
            }
        },
        "waveforms": {
            "r1$readout$wf$I": {"sample": 0.1, "type": "constant"},
            "r1$readout$wf$Q": {"sample": 0.0, "type": "constant"},
        },
    }
    assert cfg == expected_cfg
