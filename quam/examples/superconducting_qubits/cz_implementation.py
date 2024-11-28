from quam.core import quam_dataclass
from quam.components.pulses import Pulse
from quam.components.macro import QubitPairMacro


@quam_dataclass
class CZImplementation(QubitPairMacro):
    """CZ Operation for a qubit pair"""

    flux_pulse: Pulse

    phase_shift_control: float = 0.0
    phase_shift_target: float = 0.0

    def apply(self, *, amplitude_scale=None):
        self.flux_pulse.play(amplitude_scale=amplitude_scale)
        self.qubit_control.align(self.qubit_target)
        self.qubit_control.xy.frame_rotation(self.phase_shift_control)
        self.qubit_target.xy.frame_rotation(self.phase_shift_target)
        self.qubit_pair.align()
