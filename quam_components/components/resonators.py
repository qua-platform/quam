import numpy as np
from typing import Union
from dataclasses import dataclass

from quam_components import QuamComponent
from .general import Mixer


__all__ = ["ReadoutResonator"]


@dataclass(kw_only=True, eq=False)
class ReadoutResonator(QuamComponent):
    id: Union[int, str]
    mixer: Mixer
    readout_length: int = None
    readout_amplitude: float = None
    frequency_opt: float = None
    frequency_res: float = None
    time_of_flight: int = None
    smearing: int = 0
    rotation_angle: float = None

    controller: str = "con1"

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"res{self.id}"

    def calculate_integration_weights(self):
        integration_weights = {
            f"cosine_weights_{self.name}": {
                "cosine": [(1.0, self.readout_length)],
                "sine": [(0.0, self.readout_length)],
            },
            f"sine_weights_{self.name}": {
                "cosine": [(0.0, self.readout_length)],
                "sine": [(1.0, self.readout_length)],
            },
            # Why is there no minus cosine?
            f"minus_sine_weights_{self.name}": {
                "cosine": [(0.0, self.readout_length)],
                "sine": [(-1.0, self.readout_length)],
            },
        }
        if self.rotation_angle is not None:
            integration_weights[f"rotated_cosine_weights_{self.name}"] = {
                "cosine": [(np.cos(self.rotation_angle), self.readout_length)],
                "sine": [(-np.sin(self.rotation_angle), self.readout_length)],
            }
            integration_weights[f"rotated_sine_weights_{self.name}"] = {
                "cosine": [(np.sin(self.rotation_angle), self.readout_length)],
                "sine": [(np.cos(self.rotation_angle), self.readout_length)],
            }
            integration_weights[f"rotated_minus_sine_weights_{self.name}"] = {
                "cosine": [(-np.sin(self.rotation_angle), self.readout_length)],
                "sine": [(-np.cos(self.rotation_angle), self.readout_length)],
            }
        return integration_weights

    def calculate_waveforms(self):
        return {
            f"readout_{self.name}_wf": {
                "type": "constant",
                "sample": self.readout_amplitude,
            }
        }

    def calculate_pulses(self):
        integration_weights_labels = ["cos", "sin", "minus_sin"]
        if self.rotation_angle is None:
            integration_weights_labels += [
                "rotated_cos",
                "rotated_sin",
                "rotated_minus_sin",
            ]
        integration_weights_mapping = dict(
            zip(integration_weights_labels, self.calculate_integration_weights().keys())
        )

        return {
            f"readout_pulse_q{self.id}": {
                "operation": "measurement",
                "length": self.readout_pulse_length,
                "waveforms": {
                    "I": f"readout_{self.name}_wf",
                    "Q": "zero_wf",
                },
                "integration_weights": integration_weights_mapping,
                "digital_marker": "ON",
            }
        }

    def apply_to_config(self, config: dict):
        config["elements"][self.name] = {
            "mixInputs": self.mixer.get_input_config(),
            "intermediate_frequency": self.mixer.intermediate_frequency,
            "operations": {
                "cw": "const_pulse",
                "readout": f"readout_pulse_q{self.id}",
            },
            "outputs": {
                "out1": (self.controller, self.mixer.port_I),
                "out2": (self.controller, self.mixer.port_Q),
            },
            "smearing": self.smearing,
        }

        if self.time_of_flight is not None:
            config["elements"][self.name]["time_of_flight"] = self.time_of_flight

        integration_weights = self.calculate_integration_weights()
        config["integration_weights"].update(integration_weights)
        waveforms = self.calculate_waveforms()
        config["waveforms"].update(waveforms)
