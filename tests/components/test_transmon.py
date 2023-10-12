from dataclasses import dataclass
from quam.components import *
from quam.core import QuamRoot


def test_basic_transmon():
    transmon = Transmon(id=1)
    assert transmon.name == "q1"
    assert transmon.id == 1
    assert transmon.xy is None
    assert transmon.z is None

    transmon.id = "Q1"
    assert transmon.name == "Q1"


def test_transmon_xy():
    transmon = Transmon(
        id=1,
        xy=IQChannel(
            mixer=Mixer(),
            output_port_I=("con1", 1),
            output_port_Q=("con1", 2),
            local_oscillator=LocalOscillator(frequency=5e9),
            intermediate_frequency=100e6,
        ),
    )

    assert transmon.xy.name == "q1$xy"
    assert transmon.xy.mixer.name == "q1$xy$mixer"
    assert not transmon.xy.operations
    assert transmon.xy.mixer.intermediate_frequency == 100e6
    assert transmon.z is None

    cfg = {"controllers": {}, "elements": {}}

    transmon.xy.mixer.local_oscillator_frequency = 5e9

    assert transmon.xy.frequency_rf == 5.1e9

    transmon.xy.apply_to_config(cfg)
    expected_cfg = {
        "elements": {
            "q1$xy": {
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "q1$xy$mixer",
                },
                "intermediate_frequency": 100e6,
                "operations": {},
            },
        },
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.0}, 2: {"offset": 0.0}},
                "digital_outputs": {},
                "analog_inputs": {},
            }
        },
    }
    assert cfg == expected_cfg


def test_transmon_add_pulse():
    transmon = Transmon(
        id=1,
        xy=IQChannel(
            mixer=Mixer(),
            output_port_I=("con1", 1),
            output_port_Q=("con1", 2),
            local_oscillator=LocalOscillator(frequency=5e9),
            intermediate_frequency=100e6,
        ),
    )
    transmon.xy.operations["X180"] = pulses.DragPulse(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20, rotation_angle=0
    )

    quam_dict = transmon.to_dict()
    expected_quam_dict = {
        "id": 1,
        "xy": {
            "mixer": {},
            "local_oscillator": {"frequency": 5000000000.0},
            "intermediate_frequency": 100000000.0,
            "output_port_I": ("con1", 1),
            "output_port_Q": ("con1", 2),
            "operations": {
                "X180": {
                    "__class__": "quam.components.pulses.DragPulse",
                    "amplitude": 1,
                    "sigma": 4,
                    "alpha": 2,
                    "anharmonicity": 200000000.0,
                    "rotation_angle": 0.0,
                    "length": 20,
                }
            },
        },
    }
    assert quam_dict == expected_quam_dict

    config = {"controllers": {}, "elements": {}, "pulses": {}, "waveforms": {}}
    transmon.xy.apply_to_config(config)

    assert config == {
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.0}, 2: {"offset": 0.0}},
                "digital_outputs": {},
                "analog_inputs": {},
            }
        },
        "elements": {
            "q1$xy": {
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 5000000000.0,
                    "mixer": "q1$xy$mixer",
                },
                "intermediate_frequency": 100e6,
                "operations": {"X180": "q1$xy$X180$pulse"},
            },
        },
        "pulses": {},
        "waveforms": {},
    }

    config = {"controllers": {}, "elements": {}, "pulses": {}, "waveforms": {}}
    transmon.xy.operations["X180"].apply_to_config(config)

    from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

    I, Q = drag_gaussian_pulse_waveforms(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20
    )
    expected_cfg = {
        "controllers": {},
        "elements": {},
        "pulses": {
            "q1$xy$X180$pulse": {
                "operation": "control",
                "length": 20,
                "waveforms": {"I": "q1$xy$X180$wf$I", "Q": "q1$xy$X180$wf$Q"},
            },
        },
        "waveforms": {
            "q1$xy$X180$wf$I": {"type": "arbitrary", "samples": I},
            "q1$xy$X180$wf$Q": {"type": "arbitrary", "samples": Q},
        },
    }
    assert config == expected_cfg


@dataclass
class QuamTestSingle(QuamRoot):
    qubit: Transmon


quam_dict_single = {"qubit": {"id": 0}}


quam_dict_single_nested = {
    "qubit": {
        "id": 0,
        "xy": {
            "mixer": {},
            "output_port_I": ("con1", 0),
            "output_port_Q": ("con1", 1),
            "intermediate_frequency": 100e6,
            "local_oscillator": {"power": 10, "frequency": 6e9},
        },
    }
}


def test_instantiation_single_element():
    quam = QuamTestSingle.load(quam_dict_single)

    assert isinstance(quam.qubit, Transmon)
    assert quam.qubit.id == 0
    assert quam.qubit.xy is None

    assert quam.qubit._root is quam


def test_instantiation_single_nested_element():
    quam = QuamTestSingle.load(quam_dict_single_nested)

    assert quam.qubit.xy.mixer.name == "q0$xy$mixer"
    assert quam.qubit.xy.mixer.local_oscillator_frequency == 6e9

    assert quam.qubit._root is quam
    assert quam.qubit.xy._root is quam
    assert quam.qubit.xy.mixer._root is quam
