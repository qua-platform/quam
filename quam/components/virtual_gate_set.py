from dataclasses import dataclass, field
import numpy as np
from typing import ClassVar, Dict, List, Optional, Tuple, Union

from quam.components.hardware import LocalOscillator, Mixer, FrequencyConverter
from quam.components.pulses import Pulse
from quam.components.channels import SingleChannel
from quam.core import QuamComponent
from quam.utils import string_reference as str_ref

from quam.utils import patch_dataclass

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10

__all__ = ["VirtualGateSet"]


@dataclass(kw_only=True, eq=False)
class VirtualGateSet(QuamComponent):
    gates: List[SingleChannel]
    virtual_gates: Dict[str, List[float]]

    # Not sure if I should implement it this way
    pulses: Dict[str, Dict[str, float]] = field(default_factory=dict)

    @property
    def apply_config_after(self):
        return self.gates

    def add_pulse(self, pulse_name: str, pulse_type: type, **virtual_gate_voltages): ...

    def convert_voltages(self, **virtual_gate_voltages):
        gate_voltages = np.zeros(len(self.gates))
        for virtual_gate_name, voltage in virtual_gate_voltages.items():
            scales = self.virtual_gates[virtual_gate_name]
            gate_voltages += voltage * np.array(scales)

        return gate_voltages

    def play(self, pulse_name):
        for gate in self.gates:
            gate.play(pulse_name)


gate1.play("pulse_0.1V")
gate2.play("pulse_0.02V")

virtual = VirtualGateSet(
  gates=[gate1, gate2], 
  virtual_gates={"eps": [0.2, 0.01], "U": [0.01, 0.5]}
  pulse_defaults=[
    SquarePulse(amplitude=0.1, length=16),  # This already includes scale
    SquarePulse(amplitude=0.2, length=16),
  ]
)
virtual.pulses["initialize"] = CombinedPulse(
  amplitudes={"eps": 0.01, "U": 0.005},
  pulses=None  # use pulse_defaults if not specified
)


# Playing pulses
virtual.play("initialize")