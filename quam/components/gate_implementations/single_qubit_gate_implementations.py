from abc import ABC, abstractmethod
from quam.components.pulses import Pulse
from quam.core import quam_dataclass, QuamComponent


@quam_dataclass
class SingleQubitGateImplementation(QuamComponent, ABC):
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
class SinglePulseGateImplementation(SingleQubitGateImplementation):
    """Single-qubit gate for a qubit consisting of a single pulse

    Args:
        pulse: Name of pulse to be played on qubit. Should be a key in
            `channel.operations` for one of the qubit's channels

    """

    pulse: Pulse

    def execute(self, *, amplitude_scale=None, duration=None, **kwargs):
        self.pulse.play(amplitude_scale=amplitude_scale, duration=duration, **kwargs)
