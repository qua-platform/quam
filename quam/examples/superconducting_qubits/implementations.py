from copy import copy

from quam.core import quam_dataclass
from quam.components.pulses import Pulse
from quam.components.implementations import QubitPairImplementation
from quam.utils import string_reference as str_ref


@quam_dataclass
class CZImplementation(QubitPairImplementation):
    """CZ Operation for a qubit pair"""

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

    def apply(self, *, amplitude_scale=None):
        self.qubit_control.z.play(
            self.flux_pulse_control_label,
            validate=False,
            amplitude_scale=amplitude_scale,
        )
        self.qubit_control.align(self.qubit_target)

        self.qubit_control.xy.frame_rotation(self.phase_shift_control)
        self.qubit_target.xy.frame_rotation(self.phase_shift_target)
        self.qubit_pair.align()

    @property
    def config_settings(self):
        return {"after": [self.qubit_control.z]}

    def apply_to_config(self, config: dict) -> None:
        if self.flux_pulse_control.parent is self:

            pulse = copy(self.flux_pulse_control)
            pulse.id = self.flux_pulse_control_label
            pulse.parent = None  # Reset parent so it can be attached to new parent
            pulse.parent = self.qubit_control.z

            self.flux_pulse_control.apply_to_config(config)

            element_config = config["elements"][self.qubit_control.z.name]
            element_config["operations"][
                self.flux_pulse_control_label
            ] = pulse.pulse_name
