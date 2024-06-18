from abc import ABC, abstractmethod
from typing import Dict
from dataclasses import field
from copy import copy

from quam.components.pulses import Pulse
from quam.core import quam_dataclass, QuamComponent
from quam.utils import string_reference as str_ref


__all__ = ["TwoQubitGate", "CZGate"]


@quam_dataclass
class TwoQubitGate(QuamComponent, ABC):
    @property
    def qubit_pair(self):
        from ..qubit_pair import QubitPair

        if isinstance(self.parent, QubitPair):
            return self.parent
        elif hasattr(self.parent, "parent") and isinstance(
            self.parent.parent, QubitPair
        ):
            return self.parent.parent
        else:
            raise AttributeError(
                "TwoQubitGate is not attached to a QubitPair. 2Q_gate: {self}"
            )

    @property
    def qubit_control(self):
        return self.qubit_pair.qubit_control

    @property
    def qubit_target(self):
        return self.qubit_pair.qubit_target

    def __call__(self):
        self.execute()


@quam_dataclass
class CZGate(TwoQubitGate):
    """CZ Operation for a qubit pair"""

    # Pulses will be added to qubit elements
    # The reason we don't add "flux_to_q1" directly to q1.z is because it is part of
    # the CZ operation, i.e. it is only applied as part of a CZ operation

    flux_pulse_control: Pulse

    phase_shift_control: float = 0.0
    phase_shift_target: float = 0.0

    @property
    def gate_label(self) -> str:
        try:
            return self.parent.get_attr_name(self)
        except AttributeError:
            return "CZ"

    @property
    def flux_pulse_control_label(self) -> str:
        if self.flux_pulse_control.id is not None:
            pulse_label = self.flux_pulse_control.id
        else:
            pulse_label = "flux_pulse_control"

        return f"{self.gate_label}{str_ref.DELIMITER}{pulse_label}"

    def execute(self, amplitude_scale=None):
        self.qubit_control.z.play(
            self.flux_pulse_control_label,
            validate=False,
            amplitude_scale=amplitude_scale,
        )
        self.qubit_control.align(self.qubit_target)

        self.qubit_control.xy.frame_rotation(self.phase_shift_control)
        self.qubit_target.xy.frame_rotation(self.phase_shift_target)
        self.qubit_control.align(self.qubit_target)

    @property
    def config_settings(self):
        return {"after": [self.qubit_control.z]}

    def apply_to_config(self, config: dict) -> None:
        pulse = copy(self.flux_pulse_control)
        pulse.id = self.flux_pulse_control_label
        pulse.parent = None  # Reset parent so it can be attached to new parent
        pulse.parent = self.qubit_control.z

        if self.flux_pulse_control_label in self.qubit_control.z.operations:
            raise ValueError(
                "Pulse name already exists in pulse operations. "
                f"Channel: {self.qubit_control.z.get_reference()}, "
                f"Pulse: {self.flux_pulse_control.get_reference()}, "
                f"Pulse name: {self.flux_pulse_control_label}"
            )

        pulse.apply_to_config(config)

        element_config = config["elements"][self.qubit_control.z.name]
        element_config["operations"][self.flux_pulse_control_label] = pulse.pulse_name
