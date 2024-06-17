from abc import ABC, abstractmethod
from typing import Dict
from dataclasses import field
from quam.core import quam_dataclass, QuamComponent
from quam.components.pulses import Pulse


@quam_dataclass
class SingleQubitGate(QuamComponent, ABC):
    @property
    def qubit(self):
        from ..qubit import Qubit

        if isinstance(self.parent, Qubit):
            return self.parent
        elif hasattr(self.parent, "parent") and isinstance(self.parent.parent, Qubit):
            return self.parent.parent
        else:
            raise AttributeError(
                "SingleQubitGate is not attached to a qubit. 1Q_gate: {self}"
            )

    def __call__(self):
        self.execute()

    @abstractmethod
    def execute(self, *args, **kwargs):  # TODO Accomodate differing arguments
        pass


@quam_dataclass
class SinglePulseGate(SingleQubitGate):
    """Single-qubit gate for a qubit consisting of a single pulse"""

    pulse_label: str

    def execute(self, amplitude_scale=None, duration=None):
        self.qubit.xy.play(  # TODO Introduce a "play" method to the qubit
            self.pulse_label, amplitude_scale=amplitude_scale, duration=duration
        )
