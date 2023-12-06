from copy import copy
from dataclasses import dataclass, field
import numpy as np
from typing import Dict, List

from quam.components.pulses import Pulse
from quam.components.channels import SingleChannel
from quam.core import QuamComponent, quam_dataclass


__all__ = ["VirtualPulse", "VirtualGateSet"]


@quam_dataclass
class VirtualPulse(Pulse):
    amplitudes: Dict[str, float]
    # pulses: List[Pulse] = None  # Should be added later

    @property
    def virtual_gate_set(self):
        virtual_gate_set = self.parent.parent
        assert isinstance(virtual_gate_set, VirtualGateSet)
        return virtual_gate_set

    def waveform_function(self): ...


@quam_dataclass
class VirtualGateSet(QuamComponent):
    gates: List[SingleChannel]
    virtual_gates: Dict[str, List[float]]

    pulse_defaults: List[Pulse] = field(default_factory=list)
    operations: Dict[str, VirtualPulse] = field(default_factory=dict)

    @property
    def config_settings(self):
        return {"after": self.gates}

    def convert_amplitudes(self, **virtual_gate_amplitudes):
        gate_amplitudes = np.zeros(len(self.gates))
        for virtual_gate_name, amplitude in virtual_gate_amplitudes.items():
            scales = self.virtual_gates[virtual_gate_name]
            gate_amplitudes += amplitude * np.array(scales)

        return gate_amplitudes

    def play(self, pulse_name):
        for gate in self.gates:
            gate.play(pulse_name, validate=False)

    def apply_to_config(self, config: dict) -> None:
        for operation_name, operation in self.operations.items():
            gate_pulses = [copy(pulse) for pulse in self.pulse_defaults]
            gate_amplitudes = self.convert_amplitudes(**operation.amplitudes)

            for gate, pulse, amplitude in zip(self.gates, gate_pulses, gate_amplitudes):
                pulse.id = operation_name
                pulse.amplitude = amplitude
                pulse.length = operation.length
                pulse.parent = None  # Reset parent so it can be attached to new parent
                pulse.parent = gate
                pulse.apply_to_config(config)

                element_config = config["elements"][gate.name]
                element_config["operations"][operation_name] = pulse.name
