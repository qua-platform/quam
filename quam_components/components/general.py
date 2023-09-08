import numbers
import numpy as np
from typing import Dict, List, Union
from dataclasses import dataclass, field

from quam_components.core import QuamComponent
from quam_components.components.pulses import Pulse


__all__ = ["LocalOscillator", "Mixer", "AnalogInput", "IQChannel", "SingleChannel"]


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

        config["mixers"][self.name] = [
            {
                "intermediate_frequency": self.intermediate_frequency,
                "lo_frequency": self.local_oscillator.frequency,
                "correction": correction_matrix,
            }
        ]

        analog_outputs = config["controllers"][self.controller]["analog_outputs"]
        analog_outputs[self.port_I] = {"offset": self.offset_I}
        analog_outputs[self.port_Q] = {"offset": self.offset_Q}

    @staticmethod
    def IQ_imbalance(g: float, phi: float) -> List[float]:
        """
        Creates the correction matrix for the mixer imbalance caused by the gain and
        phase imbalances, more information can be seen here:
        https://docs.qualang.io/libs/examples/mixer-calibration/#non-ideal-mixer
        :param g: relative gain imbalance between the I & Q ports. (unit-less),
            set to 0 for no gain imbalance.
        :param phi: relative phase imbalance between the I & Q ports (radians),
            set to 0 for no phase imbalance.
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


@dataclass(kw_only=True, eq=False)
class PulseEmitter(QuamComponent):
    pulses: Dict[str, Pulse] = field(default_factory=dict)

    @property
    def pulse_mapping(self):
        return {
            label: f"{self.name}_{label}_pulse" for label, pulse in self.pulses.items()
        }

    def play(self, pulse_name: str):
        # pulse = self.pulses[pulse_name]
        raise NotImplementedError

    def apply_to_config(self, config: dict):
        for label, pulse in self.pulses.items():
            pulse_config = pulse.get_pulse_config()
            config["pulses"][f"{self.name}_{label}_pulse"] = pulse_config

            waveform = pulse.calculate_waveform()

            if isinstance(waveform, numbers.Number):
                wf_type = "constant"
                if isinstance(waveform, numbers.complex):
                    waveforms = {"I": waveform.real, "Q": waveform.imag}
                else:
                    waveforms = {"single": waveform}
            elif isinstance(waveform, (list, np.ndarray)):
                wf_type = "arbitrary"
                if np.iscomplexobj(waveform):
                    waveforms = {"I": list(waveform.real), "Q": list(waveform.imag)}
                else:
                    waveforms = {"single": list(waveform)}

            for suffix, waveform in waveforms.items():
                waveform_name = f"{self.name}_{label}_wf"
                if suffix != "single":
                    waveform_name += f"_{suffix}"

                config["waveforms"][waveform_name] = {
                    "type": wf_type,
                    "sample": waveform,
                }
                pulse_config["waveforms"][suffix] = waveform_name


@dataclass(kw_only=True, eq=False)
class IQChannel(PulseEmitter):
    mixer: Mixer

    @property
    def name(self) -> str:
        return f"{self.parent.name}_{self._get_parent_attr_name()}"

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)

        config["elements"][self.name] = {
            "mixInputs": self.mixer.get_input_config(),
            "intermediate_frequency": self.mixer.intermediate_frequency,
            "operations": self.pulse_mapping,
        }


@dataclass(kw_only=True, eq=False)
class SingleChannel(PulseEmitter):
    port: int
    filter_fir_taps: List[float] = None
    filter_iir_taps: List[float] = None

    offset: float = 0

    controller: str = "con1"

    @property
    def name(self) -> str:
        return f"{self.parent.name}_{self._get_parent_attr_name()}"

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)

        config["elements"][self.name] = {
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
