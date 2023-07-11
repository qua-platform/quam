import numpy as np

from quam_components import QuamElement
from .general import Mixer


class Transmon(QuamElement):
    id: int
    mixer: Mixer

    frequency_01: float = None

    # Flux pulsing
    z_max_frequency_point: float = None
    z_output_port: int = None  # TODO consider moving to "wiring"

    controller: str = "con1"

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"
    
    def calculate_waveforms(self):
        ...

    def calculate_pulses(self):
        ...

    def apply_to_config(self, config: dict):
        # Add XY to "elements"
        config["elements"][f"{self.name}_xy"] = {
            "mixInputs": self.mixer.get_input_config(),
            "intermediate_frequency": (self.frequency_01 - self.mixer.local_oscillator.frequency),
            "operations": {},  # TODO add operations
        }

        # Add Z to "elements"
        config["elements"][f"{self.name}_z"] = {
            "singleInput": {
                "port": (self.controller, self.z.wiring.port),  # TODO fix wiring
            },
            "operations": {  # TODO add operations
                # "const": f"const_flux_pulse{i}",
            },
        }

        # Add analog output Z (x and y are set in mixer)
        if self.z_max_frequency_point is not None and self.z_output_port is not None:
            analog_outputs = config["controllers"][self.controller]["analog_outputs"]
            analog_outputs[self.z_output_port] = {"offset": self.z_max_frequency_point}
            
            if self.filter_fir_taps is not None and self.filter_iir_taps is not None:
                analog_outputs[self.z_output_port]["filter"].update({
                    "feedback": self.filter_iir_taps,
                    "feedforward": self.filter_fir_taps,
                })
