from copy import copy
from dataclasses import dataclass, field
import numpy as np
from typing import Dict, List

from quam.components.pulses import Pulse
from quam.components.channels import SingleChannel
from quam.core import QuamComponent

from quam.utils import patch_dataclass

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10

__all__ = ["VirtualGateSet"]


class VirtualPulse(Pulse):
    amplitudes: Dict[str, float]
    # pulses: List[Pulse] = None  # Should be added later

    @property
    def virtual_gate_set(self):
        virtual_gate_set = self.parent.parent
        assert isinstance(virtual_gate_set, VirtualGateSet)
        return virtual_gate_set


@dataclass(kw_only=True, eq=False)
class VirtualGateSet(QuamComponent):
    gates: List[SingleChannel]
    virtual_gates: Dict[str, List[float]]

    pulse_defaults: List[Pulse] = field(default_factory=list)
    operations: Dict[str, VirtualPulse] = field(default_factory=dict)

    @property
    def apply_config_after(self):
        return self.gates

    def convert_amplitudes(self, **virtual_gate_amplitudes):
        gate_amplitudes = np.zeros(len(self.gates))
        for virtual_gate_name, amplitude in virtual_gate_amplitudes.items():
            scales = self.virtual_gates[virtual_gate_name]
            gate_amplitudes += amplitude * np.array(scales)

        return gate_amplitudes

    def play(self, pulse_name):
        for gate in self.gates:
            gate.play(pulse_name)

    def apply_to_config(self, config: dict) -> None:
        for operation_name, operation in self.operations.items():
            gate_pulses = [copy(pulse) for pulse in self.pulse_defaults]
            gate_amplitudes = self.convert_amplitudes(**operation.amplitudes)

            for gate, pulse, amplitude in zip(self.gates, gate_pulses, gate_amplitudes):
                pulse.amplitude = amplitude
                pulse.parent = gate
                pulse.id = operation_name
                pulse.apply_to_config(config, gate)

                element_config = config["elements"][gate.name]
                element_config["operations"][operation_name] = pulse.name
