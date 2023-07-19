import numpy as np
from typing import List, Union
from dataclasses import dataclass

from quam_components.core import QuamComponent


__all__ = ["LocalOscillator", "Mixer", "AnalogInput"]


@dataclass(kw_only=True, eq=False)
class LocalOscillator(QuamComponent):
    power: float = None
    frequency: float = None


@dataclass(kw_only=True, eq=False)
class Mixer(QuamComponent):
    id: Union[int, str]

    local_oscillator: LocalOscillator

    port_I: int
    port_Q: int

    frequency_drive: float

    offset_I: float = 0
    offset_Q: float = 0

    correction_gain: float = 0
    correction_phase: float = 0

    controller: str = "con1"

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"mixer{self.id}"

    @property
    def intermediate_frequency(self):
        return self.frequency_drive - self.local_oscillator.frequency

    def get_input_config(self):
        return {
            "I": (self.controller, self.port_I),
            "Q": (self.controller, self.port_Q),
            "lo_frequency": self.local_oscillator.frequency,
            "mixer": self.name,
        }
        

    def apply_to_config(self, config: dict):
        correction_matrix = self.IQ_imbalance(
            self.correction_gain, self.correction_phase
        )
        
        config["mixers"][self.name] = [{
            "intermediate_frequency": self.intermediate_frequency,
            "lo_frequency": self.local_oscillator.frequency,
            "correction": correction_matrix
        }]

        analog_outputs = config["controllers"][self.controller]["analog_outputs"]
        analog_outputs[self.port_I] = {"offset": self.offset_I}
        analog_outputs[self.port_Q] = {"offset": self.offset_Q}

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
        return [
            float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]
        ]


@dataclass(kw_only=True, eq=False)
class AnalogInput(QuamComponent):
    port: int
    offset: float = 0
    gain: float = 0

    controller: str = "con1"

    def apply_to_config(self, config: dict) -> None:
        config["controllers"][self.controller]["analog_inputs"][self.port] = {
            "offset": self.offset,
            "gain_db": self.gain,
        }