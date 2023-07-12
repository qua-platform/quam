from typing import List
import numpy as np

from quam_components import QuamElement
from .general import Mixer
from quam_components.utils.pulse import pulse_str_to_axis_axis_angle


class Transmon(QuamElement):
    id: int
    mixer: Mixer

    frequency_01: float = None

    # Flux pulsing
    z_max_frequency_point: float = None
    z_output_port: int = None  # TODO consider moving to "wiring"

    xy_pulses: List[str] = [f"{axis}{angle}" for axis in "XY" for angle in ["m90", "90", "180"]]
    xy_pi_amp
    xy_pi_length
    xy_drag_coefficient
    xy_anharmonicity
    xy_ac_stark_detuning

    z_pulses: List[str] = ["const"]
    z_flux_pulse_length
    z_flux_pulse_amp

    controller: str = "con1"

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"
    
    def _get_pulse_mapping(self):
        return {pulse: f"{pulse}_{self.name}_pulse" for pulse in self.xy_pulses}
    
    def calculate_pulses_waveforms(self):
        # TODO perhaps this should logic should go into a separate class
        from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms
        pulses = {}
        waveforms = {}
        
        # Add XY pulses
        for pulse_label, pulse_name in self._get_pulse_mapping().items():
            pulses[pulse_name] = {
                "operation": "control",
                "length": self.xy_pi_length,
                "waveforms": {
                    "I": f"{pulse_label}_I_{self.name}_wf",
                    "Q": f"{pulse_label}_Q_{self.name}_wf"
                }
            }

            # Add XY waveforms
            axis, angle = pulse_str_to_axis_axis_angle(pulse_label)
            waveform, waveform_derivative = drag_gaussian_pulse_waveforms(
                amplitude=self.xy_pi_amp * angle / 180,
                length=self.xy_pi_length,
                sigma=self.xy_pi_length / 5,  # consider not hardcoding this
                alpha=self.xy_drag_coefficient,
                anharmonicity=self.xy_anharmonicity,
                detuning=self.xy_ac_stark_detuning,
            )
            waveform_I = waveform if axis == "X" else waveform_derivative
            waveforms[f"{pulse_label}_I_{self.name}_wf"] = {"type": "arbitrary", "samples": waveform_I}
            waveform_Q = waveform_derivative if axis == "X" else waveform
            waveforms[f"{pulse_label}_Q_{self.name}_wf"] = {"type": "arbitrary", "samples": waveform_Q}

            # Add flux pulses
            pulses[f"const_flux_{self.name}_pulse"] = {
                "operation": "control",
                "length": self.z_flux_pulse_length,
                "waveforms": {
                    "single": f"const_flux_{self.name}_wf",
                },
            }
            waveforms[f"const_flux_{self.name}_wf"] = {"type": "constant", "sample": self.z_flux_pulse_amp}

        return pulses, waveforms 

    def apply_to_config(self, config: dict):
        # Add XY to "elements"
        config["elements"][f"{self.name}_xy"] = {
            "mixInputs": self.mixer.get_input_config(),
            "intermediate_frequency": (self.frequency_01 - self.mixer.local_oscillator.frequency),
            "operations": self._get_pulse_mapping(),
        }

        # Add Z to "elements"
        config["elements"][f"{self.name}_z"] = {
            "singleInput": {
                "port": (self.controller, self.z.wiring.port),  # TODO fix wiring
            },
            "operations": {
                "const": f"const_flux_pulse_{self.name}",
            },
        }

        # Add analog output Z (XY output is set in mixer)
        if self.z_max_frequency_point is not None and self.z_output_port is not None:
            analog_outputs = config["controllers"][self.controller]["analog_outputs"]
            analog_outputs[self.z_output_port] = {"offset": self.z_max_frequency_point}
            
            if self.filter_fir_taps is not None and self.filter_iir_taps is not None:
                analog_outputs[self.z_output_port]["filter"].update({
                    "feedback": self.filter_iir_taps,
                    "feedforward": self.filter_fir_taps,
                })

        pulses, waveforms = self.calculate_pulses_waveforms()
        config["pulses"].update(pulses)
        config["waveforms"].update(waveforms)