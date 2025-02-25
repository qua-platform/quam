import pytest
from quam.components import *
from quam.components.ports.analog_inputs import OPXPlusAnalogInputPort
from quam.components.ports.analog_outputs import OPXPlusAnalogOutputPort


def test_empty_in_out_IQ_channel():
    readout_resonator = InOutIQChannel(
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        opx_input_I=("con1", 3),
        opx_input_Q=("con1", 4),
        intermediate_frequency=100e6,
    )

    assert isinstance(readout_resonator.frequency_converter_up.mixer, Mixer)

    assert isinstance(readout_resonator.local_oscillator, LocalOscillator)
    assert (
        readout_resonator.frequency_converter_up.local_oscillator
        is readout_resonator.local_oscillator
    )

    mixer = readout_resonator.frequency_converter_up.mixer
    assert mixer.intermediate_frequency == 100e6

    assert mixer.local_oscillator_frequency is None
    readout_resonator.local_oscillator.frequency = 5e9
    assert mixer.local_oscillator_frequency == 5e9

    with pytest.raises(AttributeError):
        mixer.name
    assert readout_resonator.id is None
    with pytest.raises(AttributeError):
        readout_resonator.name

    readout_resonator.id = 1

    d = readout_resonator.to_dict()
    assert d == {
        "frequency_converter_up": {
            "__class__": "quam.components.hardware.FrequencyConverter",
            "mixer": {},
            "local_oscillator": {"frequency": 5000000000.0},
        },
        "opx_output_I": ("con1", 1),
        "opx_output_Q": ("con1", 2),
        "opx_input_I": ("con1", 3),
        "opx_input_Q": ("con1", 4),
        "intermediate_frequency": 100000000.0,
        "id": 1,
    }

    bare_cfg = {
        "controllers": {},
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
    }
    cfg = bare_cfg.copy()
    expected_cfg = {
        "controllers": {
            "con1": {
                "analog_inputs": {
                    3: {"gain_db": 0, "shareable": False},
                    4: {"gain_db": 0, "shareable": False},
                },
                "analog_outputs": {
                    1: {"delay": 0, "shareable": False},
                    2: {"delay": 0, "shareable": False},
                },
            }
        },
        "elements": {
            "IQ1": {
                "intermediate_frequency": 100000000.0,
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "IQ1.mixer",
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

    cfg = bare_cfg.copy()
    readout_resonator._default_label = "res"
    readout_resonator.apply_to_config(cfg)
    expected_cfg["elements"]["res1"] = expected_cfg["elements"].pop("IQ1")
    expected_cfg["elements"]["res1"]["mixInputs"]["mixer"] = "IQ1.mixer"

    cfg = bare_cfg.copy()
    readout_resonator.id = "resonator_1"
    readout_resonator.apply_to_config(cfg)
    expected_cfg["elements"]["resonator_1"] = expected_cfg["elements"].pop("res1")
    expected_cfg["elements"]["resonator_1"]["mixInputs"]["mixer"] = "resonator_1.mixer"


def test_readout_resonator_with_readout():
    readout_resonator = InOutIQChannel(
        id=1,
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        opx_input_I=("con1", 3),
        opx_input_Q=("con1", 4),
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator(frequency=5e9)
        ),
    )
    readout_resonator.operations["readout"] = pulses.SquareReadoutPulse(
        amplitude=0.1, length=1000
    )

    d = readout_resonator.to_dict()
    assert d == {
        "frequency_converter_up": {
            "__class__": "quam.components.hardware.FrequencyConverter",
            "mixer": {},
            "local_oscillator": {"frequency": 5000000000.0},
        },
        "opx_output_I": ("con1", 1),
        "opx_output_Q": ("con1", 2),
        "opx_input_I": ("con1", 3),
        "opx_input_Q": ("con1", 4),
        "intermediate_frequency": 100000000.0,
        "id": 1,
        "operations": {
            "readout": {
                "__class__": "quam.components.pulses.SquareReadoutPulse",
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
                    3: {"gain_db": 0, "shareable": False},
                    4: {"gain_db": 0, "shareable": False},
                },
                "analog_outputs": {
                    1: {"delay": 0, "shareable": False},
                    2: {"delay": 0, "shareable": False},
                },
            }
        },
        "elements": {
            "IQ1": {
                "intermediate_frequency": 100000000.0,
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "IQ1.mixer",
                },
                "outputs": {"out1": ("con1", 3), "out2": ("con1", 4)},
                "smearing": 0,
                "time_of_flight": 24,
                "operations": {"readout": "IQ1.readout.pulse"},
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
            "IQ1.readout.iw1": {"cosine": [(1.0, 1000)], "sine": [(-0.0, 1000)]},
            "IQ1.readout.iw2": {"cosine": [(0.0, 1000)], "sine": [(1.0, 1000)]},
            "IQ1.readout.iw3": {"cosine": [(-0.0, 1000)], "sine": [(-1.0, 1000)]},
        },
        "pulses": {
            "IQ1.readout.pulse": {
                "digital_marker": "ON",
                "integration_weights": {
                    "iw1": "IQ1.readout.iw1",
                    "iw2": "IQ1.readout.iw2",
                    "iw3": "IQ1.readout.iw3",
                },
                "length": 1000,
                "operation": "measurement",
                "waveforms": {"I": "IQ1.readout.wf.I", "Q": "IQ1.readout.wf.Q"},
            }
        },
        "waveforms": {
            "IQ1.readout.wf.I": {"sample": 0.1, "type": "constant"},
            "IQ1.readout.wf.Q": {"sample": 0.0, "type": "constant"},
        },
    }
    assert cfg == expected_cfg


def test_channel_measure(mocker):
    readout_resonator = InOutIQChannel(
        id=1,
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        opx_input_I=("con1", 3),
        opx_input_Q=("con1", 4),
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator(frequency=5e9)
        ),
    )
    readout_resonator.operations["readout"] = pulses.SquareReadoutPulse(
        amplitude=0.1, length=1000
    )

    mocker.patch("quam.components.channels.declare", return_value=1)
    mocker.patch("quam.components.channels.measure", return_value=1)
    result = readout_resonator.measure("readout")
    assert result == (1, 1)


def test_empty_in_out_IQ_channel_ports():
    readout_resonator = InOutIQChannel(
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
        opx_output_I=OPXPlusAnalogOutputPort("con1", 1),
        opx_output_Q=OPXPlusAnalogOutputPort("con1", 2),
        opx_input_I=OPXPlusAnalogInputPort("con1", 3),
        opx_input_Q=OPXPlusAnalogInputPort("con1", 4),
        intermediate_frequency=100e6,
    )

    assert isinstance(readout_resonator.frequency_converter_up.mixer, Mixer)

    assert isinstance(readout_resonator.local_oscillator, LocalOscillator)
    assert (
        readout_resonator.frequency_converter_up.local_oscillator
        is readout_resonator.local_oscillator
    )

    mixer = readout_resonator.frequency_converter_up.mixer
    assert mixer.intermediate_frequency == 100e6

    assert mixer.local_oscillator_frequency is None
    readout_resonator.local_oscillator.frequency = 5e9
    assert mixer.local_oscillator_frequency == 5e9

    with pytest.raises(AttributeError):
        mixer.name
    assert readout_resonator.id is None
    with pytest.raises(AttributeError):
        readout_resonator.name

    readout_resonator.id = 1

    d = readout_resonator.to_dict()
    assert d == {
        "frequency_converter_up": {
            "__class__": "quam.components.hardware.FrequencyConverter",
            "mixer": {},
            "local_oscillator": {"frequency": 5000000000.0},
        },
        "opx_output_I": {
            "controller_id": "con1",
            "port_id": 1,
            "__class__": "quam.components.ports.analog_outputs.OPXPlusAnalogOutputPort",
        },
        "opx_output_Q": {
            "controller_id": "con1",
            "port_id": 2,
            "__class__": "quam.components.ports.analog_outputs.OPXPlusAnalogOutputPort",
        },
        "opx_input_I": {
            "controller_id": "con1",
            "port_id": 3,
            "__class__": "quam.components.ports.analog_inputs.OPXPlusAnalogInputPort",
        },
        "opx_input_Q": {
            "controller_id": "con1",
            "port_id": 4,
            "__class__": "quam.components.ports.analog_inputs.OPXPlusAnalogInputPort",
        },
        "intermediate_frequency": 100000000.0,
        "id": 1,
    }

    bare_cfg = {
        "controllers": {},
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "integration_weights": {},
    }
    cfg = bare_cfg.copy()
    expected_cfg = {
        "controllers": {
            "con1": {
                "analog_inputs": {
                    3: {"gain_db": 0, "shareable": False},
                    4: {"gain_db": 0, "shareable": False},
                },
                "analog_outputs": {
                    1: {"delay": 0, "shareable": False},
                    2: {"delay": 0, "shareable": False},
                },
            }
        },
        "elements": {
            "IQ1": {
                "intermediate_frequency": 100000000.0,
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "IQ1.mixer",
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
    readout_resonator.opx_output_I.apply_to_config(cfg)
    readout_resonator.opx_output_Q.apply_to_config(cfg)
    readout_resonator.opx_input_I.apply_to_config(cfg)
    readout_resonator.opx_input_Q.apply_to_config(cfg)
    assert cfg == expected_cfg

    cfg = bare_cfg.copy()
    readout_resonator._default_label = "res"
    readout_resonator.apply_to_config(cfg)
    expected_cfg["elements"]["res1"] = expected_cfg["elements"].pop("IQ1")
    expected_cfg["elements"]["res1"]["mixInputs"]["mixer"] = "IQ1.mixer"

    cfg = bare_cfg.copy()
    readout_resonator.id = "resonator_1"
    readout_resonator.apply_to_config(cfg)
    expected_cfg["elements"]["resonator_1"] = expected_cfg["elements"].pop("res1")
    expected_cfg["elements"]["resonator_1"]["mixInputs"]["mixer"] = "resonator_1.mixer"
