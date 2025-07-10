from abc import ABC
from typing import Optional, Union, List
from quam.core.macro import QuamMacro
from quam.components.pulses import Pulse
from quam.core import quam_dataclass


__all__ = ["QubitMacro", "PulseMacro"]


@quam_dataclass
class QubitMacro(QuamMacro, ABC):
    @property
    def qubit(self):
        from quam.components.quantum_components.qubit import Qubit

        if isinstance(self.parent, Qubit):
            return self.parent
        elif hasattr(self.parent, "parent") and isinstance(self.parent.parent, Qubit):
            return self.parent.parent
        else:
            raise AttributeError("QubitOperation is not attached to a qubit: {self}")


@quam_dataclass
class PulseMacro(QubitMacro):
    """Single-qubit gate for a qubit consisting of a single pulse

    Args:
        pulse: Name of pulse to be played on qubit. Should be a key in
            `channel.operations` for one of the qubit's channels
    """

    pulse: Union[Pulse, str]  # type: ignore

    def apply(self, *, amplitude_scale=None, duration=None, **kwargs):
        if isinstance(self.pulse, Pulse):
            pulse = self.pulse
        else:
            pulse = self.qubit.get_pulse(self.pulse)
        pulse.play(
            amplitude_scale=amplitude_scale, duration=duration, **kwargs  # type: ignore
        )

    @property
    def inferred_duration(self) -> float:
        if isinstance(self.pulse, Pulse):
            return self.pulse.length * 1e-9
        else:
            return self.qubit.get_pulse(self.pulse).length * 1e-9
    
