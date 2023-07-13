import numpy as np
from typing import List
from dataclasses import dataclass

from quam_components.core import QuamElement


@dataclass
class LocalOscillator(QuamElement):
    power: float = None
    frequency: float = None


@dataclass
class Mixer(QuamElement):
    name: str

    local_oscillator: LocalOscillator

    frequency_drive: float = None

    I_output_port: int = None  # TODO consider moving to "wiring"
    Q_output_port: int = None  # TODO consider moving to "wiring"

    correction_gain: float = None
    correction_phase: float = None

    controller: str = "con1"

    @property
    def intermediate_frequency(self):
        return self.frequency_drive - self.local_oscillator.frequency
    
    def get_input_config(self):
        return { 
            "I": (self.controller, self.wiring.I),  # TODO fix wiring
            "Q": (self.controller, self.wiring.Q),
            "lo_frequency": self.local_oscillator.frequency,
            "mixer": self.name,
        },

    def apply_to_config(self, config: dict):
        config["mixers"][self.name] = {
            "intermediate_frequency": self.intermediate_frequency,
            "lo_frequency": self.local_oscillator.frequency,
        }

        if self.correction_gain is not None and self.correction_phase is not None:
            correction_matrix = self.IQ_imbalance(self.correction_gain, self.correction_phase)
            config["mixers"][self.name]["correction"] = correction_matrix

        analog_outputs = config["controllers"][self.controller]["analog_outputs"]
        analog_outputs[self.Q_output_port] = {"offset": self.offset_Q}
        analog_outputs[self.I_output_port] = {"offset": self.offset_I}

    @staticmethod
    def IQ_imbalance(g: float, phi: float) -> List[float]:
        """
        Creates the correction matrix for the mixer imbalance caused by the gain and phase imbalances, more information can
        be seen here:
        https://docs.qualang.io/libs/examples/mixer-calibration/#non-ideal-mixer
        :param g: relative gain imbalance between the I & Q ports. (unit-less), set to 0 for no gain imbalance.
        :param phi: relative phase imbalance between the I & Q ports (radians), set to 0 for no phase imbalance.
        """
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]