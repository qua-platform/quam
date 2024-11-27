from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from quam.components.implementations.base_implementation import BaseImplementation
from quam.components.pulses import Pulse
from quam.core import quam_dataclass

if TYPE_CHECKING:
    from qm.qua import QuaVariableType


__all__ = ["QubitImplementation", "PulseGateImplementation"]


@quam_dataclass
class QubitImplementation(BaseImplementation, ABC):
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
class PulseGateImplementation(QubitImplementation):
    """Single-qubit gate for a qubit consisting of a single pulse

    Args:
        pulse: Name of pulse to be played on qubit. Should be a key in
            `channel.operations` for one of the qubit's channels

    """

    pulse: Pulse

    def apply(self, *, amplitude_scale=None, duration=None, **kwargs):
        self.pulse.play(amplitude_scale=amplitude_scale, duration=duration, **kwargs)


@quam_dataclass
class MeasureImplementation(QubitImplementation):

    def apply(self, **kwargs) -> QuaVariableType:
        return self.qubit.measure(**kwargs)


@quam_dataclass
class AlignImplementation(QubitImplementation):
    def apply(self, *other_qubits, **kwargs):
        self.qubit.align(*other_qubits, **kwargs)


@quam_dataclass
class ResetImplementation(QubitImplementation):
    def apply(self, **kwargs):
        self.qubit.reset(**kwargs)
