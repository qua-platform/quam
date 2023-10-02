import pytest
from dataclasses import dataclass
from copy import deepcopy
from quam_components.components import *
from quam_components.core import QuamRoot


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
            mixer=Mixer(
                id=1,
                port_I=1,
                port_Q=2,
                local_oscillator=LocalOscillator(),
                intermediate_frequency=100e6,
            )
        ),
    )

    assert transmon.xy.name == "q1_xy"
    assert transmon.xy.mixer.name == "mixer1"
    assert not transmon.xy.pulses
    assert transmon.xy.mixer.intermediate_frequency == 100e6
    assert transmon.z is None

    config = {"elements": {}}
    with pytest.raises(TypeError):
        transmon.xy.mixer.frequency_rf

    transmon.xy.mixer.local_oscillator.frequency = 4.6e9

    assert transmon.xy.mixer.frequency_rf == 4.7e9

    transmon.xy.apply_to_config(config)
    assert config == {
        "elements": {
            "q1_xy": {
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 4600000000.0,
                    "mixer": "mixer1",
                },
                "intermediate_frequency": 100e6,
                "operations": {},
            },
        }
    }


def test_transmon_add_pulse():
    transmon = Transmon(
        id=1,
        xy=IQChannel(
            mixer=Mixer(
                id=1,
                port_I=1,
                port_Q=2,
                local_oscillator=LocalOscillator(frequency=4.6e9),
                intermediate_frequency=100e6,
            )
        ),
    )
    transmon.xy.pulses["X180"] = pulses.DragPulse(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20, rotation_angle=0
    )

    quam_dict = transmon.to_dict()
    assert quam_dict == {
        "id": 1,
        "xy": {
            "mixer": {
                "id": 1,
                "local_oscillator": {"frequency": 4600000000.0},
                "port_I": 1,
                "port_Q": 2,
                "intermediate_frequency": 100000000.0,
            },
            "pulses": {
                "X180": {
                    "__class__": "quam_components.components.pulses.DragPulse",
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

    config = {"elements": {}, "pulses": {}, "waveforms": {}}
    transmon.xy.apply_to_config(config)

    assert config["elements"] == {
        "q1_xy": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": 4600000000.0,
                "mixer": "mixer1",
            },
            "intermediate_frequency": 100e6,
            "operations": {"X180": "q1_xy_X180_pulse"},
        },
    }

    assert config["pulses"] == {
        "q1_xy_X180_pulse": {
            "operation": "control",
            "length": 20,
            "waveforms": {"I": "q1_xy_X180_wf_I", "Q": "q1_xy_X180_wf_Q"},
        }
    }

    from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

    I, Q = drag_gaussian_pulse_waveforms(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20
    )

    assert list(config["waveforms"]) == ["q1_xy_X180_wf_I", "q1_xy_X180_wf_Q"]
    assert config["waveforms"]["q1_xy_X180_wf_I"] == {"type": "arbitrary", "samples": I}
    assert config["waveforms"]["q1_xy_X180_wf_Q"] == {"type": "arbitrary", "samples": Q}


@dataclass
class QuamTestSingle(QuamRoot):
    qubit: Transmon


quam_dict_single = {"qubit": {"id": 0}}


quam_dict_single_nested = {
    "qubit": {
        "id": 0,
        "xy": {
            "mixer": {
                "id": 0,
                "port_I": 0,
                "port_Q": 1,
                "intermediate_frequency": 100e6,
                "local_oscillator": {"power": 10, "frequency": 6e9},
            }
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

    assert quam.qubit.xy.mixer.id == 0
    assert quam.qubit.xy.mixer.name == "mixer0"
    assert quam.qubit.xy.mixer.local_oscillator.power == 10
    assert quam.qubit.xy.mixer.local_oscillator.frequency == 6e9

    assert quam.qubit._root is quam
    assert quam.qubit.xy._root is quam
    assert quam.qubit.xy.mixer._root is quam


def test_instantiate_quam_dict():
    @dataclass
    class QuamTest(QuamRoot):
        qubit: Transmon
        wiring: dict

    quam_dict = deepcopy(quam_dict_single_nested)
    quam_dict["qubit"]["xy"]["mixer"] = {
        "id": 0,
        "port_I": ":wiring.port_I",
        "port_Q": ":wiring.port_Q",
        "intermediate_frequency": 100e6,
        "local_oscillator": {"power": 10, "frequency": 6e9},
    }
    quam_dict["wiring"] = {
        "port_I": 0,
        "port_Q": 1,
    }
    QuamTest.load(quam_dict)
