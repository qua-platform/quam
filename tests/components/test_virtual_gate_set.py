from dataclasses import field
from typing import List
import pytest

from quam.core import *
from quam.components import *


@quam_dataclass
class QuAM(QuamRoot):
    gates: List[SingleChannel] = field(default_factory=list)
    virtual_gate_set: VirtualGateSet = None


@pytest.fixture
def machine_virtual():
    machine = QuAM()
    machine.gates = [
        SingleChannel(
            id="gate1",
            opx_output=("con1", 1),
        ),
        SingleChannel(
            id="gate2",
            opx_output=("con1", 2),
        ),
    ]

    machine.virtual_gate_set = VirtualGateSet(
        gates=["#/gates/0", "#/gates/1"],
        virtual_gates={"eps": [1, 0.1], "U": [0.1, 0.8]},
        pulse_defaults=[
            pulses.SquarePulse(amplitude=0.01, length=60),
            pulses.SquarePulse(amplitude=0.01, length=60),
        ],
    )

    return machine


def test_instantiate_virtual_gate_set(machine_virtual): ...


def test_virtual_gate_set_generate_empty_config(machine_virtual):
    config = machine_virtual.generate_config()


def test_generate_config_virtual_pulse(machine_virtual):
    machine_virtual.virtual_gate_set.operations["readout"] = VirtualPulse(
        length=40, amplitudes={"eps": 1, "U": 0.5}
    )

    config = machine_virtual.generate_config()
    expected_config = {
        "controllers": {
            "con1": {
                "analog_inputs": {},
                "analog_outputs": {1: {"offset": 0}, 2: {"offset": 0}},
                "digital_outputs": {},
            }
        },
        "digital_waveforms": {"ON": {"samples": [[1, 0]]}},
        "elements": {
            "gate1": {
                "operations": {"readout": "gate1.readout"},
                "singleInput": {"port": ("con1", 1)},
            },
            "gate2": {
                "operations": {"readout": "gate2.readout"},
                "singleInput": {"port": ("con1", 2)},
            },
        },
        "integration_weights": {},
        "mixers": {},
        "oscillators": {},
        "pulses": {
            "const_pulse": {
                "length": 1000,
                "operation": "control",
                "waveforms": {"I": "const_wf", "Q": "zero_wf"},
            },
            "gate1.readout.pulse": {
                "length": 60,
                "operation": "control",
                "waveforms": {"single": "gate1.readout.wf"},
            },
            "gate2.readout.pulse": {
                "length": 60,
                "operation": "control",
                "waveforms": {"single": "gate2.readout.wf"},
            },
        },
        "version": 1,
        "waveforms": {
            "const_wf": {"sample": 0.1, "type": "constant"},
            "gate1.readout.wf": {"sample": 1.05, "type": "constant"},
            "gate2.readout.wf": {"sample": 0.5, "type": "constant"},
            "zero_wf": {"sample": 0.0, "type": "constant"},
        },
    }

    assert config == expected_config
