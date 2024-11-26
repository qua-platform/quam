from abc import ABC, abstractmethod
from quam.components.operations.base_operation import BaseOperation
from quam.components.pulses import Pulse
from quam.core import quam_dataclass


__all__ = ["QubitOperation", "QubitPulseOperation"]


@quam_dataclass
class QubitOperation(BaseOperation, ABC):
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
class QubitPulseOperation(QubitOperation):
    """Single-qubit gate for a qubit consisting of a single pulse

    Args:
        pulse: Name of pulse to be played on qubit. Should be a key in
            `channel.operations` for one of the qubit's channels

    """

    pulse: Pulse

    def execute(self, *, amplitude_scale=None, duration=None, **kwargs):
        self.pulse.play(amplitude_scale=amplitude_scale, duration=duration, **kwargs)
