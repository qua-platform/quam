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
        local_oscillator=LocalOscillator(id=2, frequency=5e9),
    )

    mixer = readout_resonator.mixer
    assert mixer.local_oscillator_frequency == 5e9
    assert mixer.intermediate_frequency == 100e6
    assert mixer.offset_I == 0
    assert mixer.offset_Q == 0

    assert readout_resonator.id == ":../id"  # parent not defined

    d = readout_resonator.to_dict()
    assert d == {
        "mixer": {},
        "output_port_I": ("con1", 1),
        "output_port_Q": ("con1", 2),
        "input_port_I": ("con1", 3),
        "input_port_Q": ("con1", 4),
        "intermediate_frequency": 100000000.0,
        "local_oscillator": {"id": 2, "frequency": 5000000000.0},
    }

    cfg = {
        "controllers": {},
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
    }
    expected_cfg = {
        "elements": {
            "r1": {
                "intermediate_frequency": 100000000.0,
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "mixer1",
                },
                "operations": {},
                "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
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
    readout_resonator = ReadoutResonator(
        id=1,
        mixer=Mixer(
            id=1,
            port_I=1,
            port_Q=2,
        ),
        intermediate_frequency=100e6,
        local_oscillator=LocalOscillator(id=2, frequency=5e9),
    )
    readout_resonator.pulses["readout"] = pulses.ReadoutPulse(
        amplitude=0.1, length=1000
    )

    d = readout_resonator.to_dict()
    assert d == {
        "id": 1,
        "mixer": {
            "id": 1,
            "port_I": 1,
            "port_Q": 2,
        },
        "intermediate_frequency": 100000000.0,
        "local_oscillator": {"id": 2, "frequency": 5000000000.0},
        "pulses": {
            "readout": {
                "__class__": "quam.components.pulses.ReadoutPulse",
                "amplitude": 0.1,
                "length": 1000,
            }
        },
    }

    cfg = {
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
        "digital_waveforms": {},
    }
    expected_cfg = {
        "elements": {
            "r1": {
                "intermediate_frequency": 100000000.0,
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "mixer1",
                },
                "operations": {"readout": "r1_readout_pulse"},
                "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
                "smearing": 0,
                "time_of_flight": 24,
            }
        },
        "pulses": {
            "r1_readout_pulse": {
                "operation": "measurement",
                "length": 1000,
                "waveforms": {
                    "I": "r1_readout_wf_I",
                    "Q": "r1_readout_wf_Q",
                },
                "integration_weights": {
                    "cosine": "r1_cosine_iw",
                    "sine": "r1_sine_iw",
                    "minus_sine": "r1_minus_sine_iw",
                },
                "digital_marker": "r1_readout_dm",
            }
        },
        "integration_weights": {
            "r1_cosine_iw": {
                "cosine": [(1.0, 1000)],
                "sine": [(0.0, 1000)],
            },
            "r1_sine_iw": {
                "cosine": [(0.0, 1000)],
                "sine": [(1.0, 1000)],
            },
            "r1_minus_sine_iw": {
                "cosine": [(0.0, 1000)],
                "sine": [(-1.0, 1000)],
            },
        },
        "waveforms": {
            "r1_readout_wf_I": {
                "type": "constant",
                "sample": 0.1,
            },
            "r1_readout_wf_Q": {
                "type": "constant",
                "sample": 0.0,
            },
        },
        "digital_waveforms": {"r1_readout_dm": {"samples": "ON"}},
    }
    readout_resonator.apply_to_config(cfg)
    assert cfg == expected_cfg
