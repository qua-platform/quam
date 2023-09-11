from quam_components.components import *


def test_empty_readout_resonator():
    readout_resonator = ReadoutResonator(
        id=1,
        mixer=Mixer(
            id=1,
            port_I=1,
            port_Q=2,
            frequency_drive=5.1e9,
            local_oscillator=LocalOscillator(frequency=5e9),
        ),
    )

    d = readout_resonator.to_dict()
    assert d == {
        "id": 1,
        "mixer": {
            "id": 1,
            "port_I": 1,
            "port_Q": 2,
            "frequency_drive": 5100000000.0,
            "local_oscillator": {"frequency": 5000000000.0},
        },
        "pulses": {},
    }

    cfg = {
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
    }
    expected_cfg = {
        "elements": {
            "res1": {
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
            frequency_drive=5.1e9,
            local_oscillator=LocalOscillator(frequency=5e9),
        ),
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
            "frequency_drive": 5100000000.0,
            "local_oscillator": {"frequency": 5000000000.0},
        },
        "pulses": {
            "readout": {
                "__class__": "quam_components.components.pulses.ReadoutPulse",
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
    }
    expected_cfg = {
        "elements": {
            "res1": {
                "intermediate_frequency": 100000000.0,
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "mixer1",
                },
                "operations": {"readout": "res1_readout_pulse"},
                "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
                "smearing": 0,
                "time_of_flight": 24,
            }
        },
        "pulses": {
            "res1_readout_pulse": {
                "operation": "measurement",
                "length": 1000,
                "waveforms": {
                    "I": "res1_readout_wf_I",
                    "Q": "res1_readout_wf_Q",
                },
                "integration_weights": {
                    "cosine": "res1_cosine_iw",
                    "sine": "res1_sine_iw",
                    "minus_sine": "res1_minus_sine_iw",
                },
                "digital_marker": "ON",
            }
        },
        "integration_weights": {
            "res1_cosine_iw": {
                "cosine": [(1.0, 1000)],
                "sine": [(0.0, 1000)],
            },
            "res1_sine_iw": {
                "cosine": [(0.0, 1000)],
                "sine": [(1.0, 1000)],
            },
            "res1_minus_sine_iw": {
                "cosine": [(0.0, 1000)],
                "sine": [(-1.0, 1000)],
            },
        },
        "waveforms": {
            "res1_readout_wf_I": {
                "type": "constant",
                "sample": 0.1,
            },
            "res1_readout_wf_Q": {
                "type": "constant",
                "sample": 0.0,
            },
        },
    }
    readout_resonator.apply_to_config(cfg)
    assert cfg == expected_cfg
