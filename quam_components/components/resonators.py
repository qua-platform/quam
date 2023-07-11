import numpy as np

from quam_components import QuamElement
from .general import Mixer


class ReadoutResonator(QuamElement):
    name: str
    mixer: Mixer
    readout_pulse_length: int = None
    frequency_opt: float = None
    frequency_res: float = None
    smearing: int = 0
    rotation_angle: float = None

    controller: str = "con1"

    def get_integration_weights(self):
        integration_weights = {
            f"cosine_weights_{self.name}": {
                "cosine": [(1.0, self.readout_pulse_length)],
                "sine": [(0.0, self.readout_pulse_length)],
            },
            f"sine_weights_{self.name}": {
                "cosine": [(0.0, self.readout_pulse_length)],
                "sine": [(1.0, self.readout_pulse_length)],
            },
            f"minus_sine_weights_{self.name}": {
                "cosine": [(0.0, self.readout_pulse_length)],
                "sine": [(-1.0, self.readout_pulse_length)],
            },
            f"minus_cosine_weights_{self.name}": {
                "cosine": [(1.0, self.readout_pulse_length)],
                "sine": [(0.0, self.readout_pulse_length)],
            },

        }
        if self.rotation_angle is not None:
            integration_weights.update({
                f"rotated_cosine_weights_{self.name}": {
                    "cosine": [(np.cos(self.rotation_angle), self.readout_pulse_length)],
                    "sine": [(-np.sin(self.rotation_angle), self.readout_pulse_length)],
                },
                f"rotated_sine_weights_{self.name}": {
                    "cosine": [(np.sin(self.rotation_angle), self.readout_pulse_length)],
                    "sine": [(np.cos(self.rotation_angle), self.readout_pulse_length)],
                },
                f"rotated_minus_sine_weights_{self.name}": {
                    "cosine": [(-np.sin(self.rotation_angle), self.readout_pulse_length)],
                    "sine": [(-np.cos(self.rotation_angle), self.readout_pulse_length)],
                },
            })

    def apply_to_config(self, config: dict):
        config["elements"][self.name] = {
            "mixInputs": {  # Should probably go to mixer
                "I": (self.controller, self.wiring.I),  # TODO fix wiring
                "Q": (self.controller, self.wiring.Q),
                "lo_frequency": self.mixer.local_oscillator.frequency,
                "mixer": self.mixer.name,
            },
            "intermediate_frequency": self.frequency_opt - self.mixer.local_oscillator.frequency,
            "operations": {  # TODO add operations
                # "cw": "const_pulse",
                # "readout": f"readout_pulse_q{i}",
            },
            "outputs": {
                "out1": (self.controller, 1),  # TODO Determine proper output ports
                "out2": (self.controller, 2),
            },
            "time_of_flight": self.global_parameters.time_of_flight,  # TODO Determine global parameters
            "smearing": 0,
        }