from typing import List, ClassVar
from dataclasses import dataclass, field

from quam_components import QuamComponent
from .general import Mixer
from quam_components.utils.pulse import pulse_str_to_axis_axis_angle


__all__ = ["Transmon", "XYChannel", "ZChannel"]


default_pulses = [f"{axis}{angle}" for axis in "XY" for angle in ["m90", "90", "180"]]


@dataclass(kw_only=True, eq=False)
class XYChannel(QuamComponent):
    mixer: Mixer

    pi_amp: float
    pi_length: float
    anharmonicity: float

    pulses: List[str] = field(default_factory=lambda: default_pulses.copy())
    drag_coefficient: float = 0
    ac_stark_detuning: float = 0

    @property
    def pulse_mapping(self):
        return {pulse: f"{pulse}_{self.parent.name}_pulse" for pulse in self.pulses}

    def calculate_pulses_waveforms(self):
        from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

        pulses = {}
        waveforms = {}

        for pulse_label, pulse_name in self.pulse_mapping.items():
            pulses[pulse_name] = {
                "operation": "control",
                "length": self.pi_length,
                "waveforms": {
                    "I": f"{pulse_label}_I_{self.parent.name}_wf",
                    "Q": f"{pulse_label}_Q_{self.parent.name}_wf",
                },
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
            waveforms[f"{pulse_label}_I_{self.parent.name}_wf"] = {
                "type": "arbitrary",
                "samples": waveform_I,
            }
            waveform_Q = waveform_derivative if axis == "X" else waveform
            waveforms[f"{pulse_label}_Q_{self.parent.name}_wf"] = {
                "type": "arbitrary",
                "samples": waveform_Q,
            }

        return pulses, waveforms

    def apply_to_config(self, config: dict):
        # Add XY to "elements"
        config["elements"][f"{self.parent.name}_xy"] = {
            "mixInputs": self.mixer.get_input_config(),
            "intermediate_frequency": self.mixer.intermediate_frequency,
            "operations": self.pulse_mapping,
        }

        pulses, waveforms = self.calculate_pulses_waveforms()
        config["pulses"].update(pulses)
        config["waveforms"].update(waveforms)


@dataclass(kw_only=True, eq=False)
class ZChannel(QuamComponent):
    port: int

    z_max_frequency_point: float = None

    pulses: List[str] = field(default_factory=lambda: ["const_flux"])
    pulse_length: float = None
    pulse_amplitude: float = None

    filter_fir_taps: List[float] = None
    filter_iir_taps: List[float] = None

    offset: float = 0

    controller: str = "con1"

    @property
    def pulse_mapping(self):
        pulse_mapping = {}
        for pulse in self.pulses:
            if pulse == "const_flux":
                if self.pulse_length is not None and self.pulse_amplitude is not None:
                    pulse_mapping[pulse] = f"const_flux_{self.parent.name}_pulse"
            else:
                raise ValueError(f"Unknown pulse {pulse}")
        return pulse_mapping

    def calculate_pulses_waveforms(self):
        pulses = {}
        waveforms = {}

        for pulse_label, pulse_name in self.pulse_mapping.items():
            if pulse_label == "const_flux":
                if self.pulse_length is None or self.pulse_amplitude is None:
                    continue
                pulses[pulse_name] = {
                    "operation": "control",
                    "length": self.pulse_length,
                    "waveforms": {
                        "single": f"const_flux_{self.parent.name}_wf",
                    },
                }
                waveforms[f"const_flux_{self.parent.name}_wf"] = {
                    "type": "constant",
                    "sample": self.pulse_amplitude,
                }

        return pulses, waveforms

    def apply_to_config(self, config: dict):
        config["elements"][f"{self.parent.name}_z"] = {
            "singleInput": {
                "port": (self.controller, self.port),
            },
            "operations": self.pulse_mapping,
        }

        analog_outputs = config["controllers"][self.controller]["analog_outputs"]
        analog_output = analog_outputs[self.port] = {"offset": self.offset}

        if self.filter_fir_taps is not None:
            output_filter = analog_output.setdefault("filter", {})
            output_filter["feedforward"] = self.filter_fir_taps

        if self.filter_iir_taps is not None:
            output_filter = analog_output.setdefault("filter", {})
            output_filter["feedback"] = self.filter_iir_taps

        pulses, waveforms = self.calculate_pulses_waveforms()
        config["pulses"].update(pulses)
        config["waveforms"].update(waveforms)


@dataclass(kw_only=True, eq=False)
class Transmon(QuamComponent):
    id: int

    frequency_01: float = None

    xy: XYChannel = None
    z: ZChannel = None

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"
