from typing import List
import numpy as np

from quam_components import QuamElement
from .general import Mixer
from quam_components.utils.pulse import pulse_str_to_axis_axis_angle


class XYChannel(QuamElement):
    mixer: Mixer
    qubit: "Transmon"

    pulses: List[str] = [f"{axis}{angle}" for axis in "XY" for angle in ["m90", "90", "180"]]
    pi_amp: float = None
    pi_length: float = None
    drag_coefficient: float = None
    anharmonicity: float = None
    ac_stark_detuning: float = None
    
    @property
    def pulse_mapping(self):
        return {pulse: f"{pulse}_{self.qubit.name}_pulse" for pulse in self.pulses}

    def calculate_pulses_waveforms(self):
        from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms
        pulses = {}
        waveforms = {}

        for pulse_label, pulse_name in self._get_pulse_mapping().items():
            pulses[pulse_name] = {
                "operation": "control",
                "length": self.pi_length,
                "waveforms": {
                    "I": f"{pulse_label}_I_{self.qubit.name}_wf",
                    "Q": f"{pulse_label}_Q_{self.qubit.name}_wf"
                }
            }

            # Add XY waveforms
            axis, angle = pulse_str_to_axis_axis_angle(pulse_label)
            waveform, waveform_derivative = drag_gaussian_pulse_waveforms(
                amplitude=self.pi_amp * angle / 180,
                length=self.pi_length,
                sigma=self.pi_length / 5,  # consider not hardcoding this
                alpha=self.drag_coefficient,
                anharmonicity=self.anharmonicity,
                detuning=self.ac_stark_detuning,
            )
            waveform_I = waveform if axis == "X" else waveform_derivative
            waveforms[f"{pulse_label}_I_{self.qubit.name}_wf"] = {"type": "arbitrary", "samples": waveform_I}
            waveform_Q = waveform_derivative if axis == "X" else waveform
            waveforms[f"{pulse_label}_Q_{self.qubit.name}_wf"] = {"type": "arbitrary", "samples": waveform_Q}

        return pulses, waveforms
    
    def apply_to_config(self, config: dict):
        # Add XY to "elements"
        config["elements"][f"{self.qubit.name}_xy"] = {
            "mixInputs": self.mixer.get_input_config(),
            "intermediate_frequency": (self.frequency_01 - self.mixer.local_oscillator.frequency),
            "operations": self.xy.pulse_mapping,
        }

        pulses, waveforms = self.calculate_pulses_waveforms()
        config["pulses"].update(pulses)
        config["waveforms"].update(waveforms)


class ZChannel(QuamElement):
    max_frequency_point: float = None
    output_port: int = None  # TODO consider moving to "wiring"

    pulses: List[str] = ["const"]
    flux_pulse_length: float = None
    flux_pulse_amp: float = None

    def add_pulses_waveforms(self):
        pulses = {}
        waveforms = {}

        # TODO iterate over pulses
        pulses[f"const_flux_{self.qubit.name}_pulse"] = {
            "operation": "control",
            "length": self.flux_pulse_length,
            "waveforms": {
                "single": f"const_flux_{self.qubit.name}_wf",
            },
        }
        waveforms[f"const_flux_{self.qubit.name}_wf"] = {"type": "constant", "sample": self.flux_pulse_amp}

        return pulses, waveforms

    def apply_to_config(self, config: dict):

        # Add to "elements"
        config["elements"][f"{self.qubit.name}_z"] = {
            "singleInput": {
                "port": (self.controller, self.z.wiring.port),  # TODO fix wiring
            },
            "operations": {
                "const": f"const_flux_pulse_{self.qubit.name}",
            },
        }

        # Add analog output
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


class Transmon(QuamElement):
    id: int

    frequency_01: float = None

    xy: XYChannel = None
    z: ZChannel = None

    controller: str = "con1"

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"
    
