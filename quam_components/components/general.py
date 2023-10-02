import numbers
import numpy as np
from typing import Dict, List, Union
from dataclasses import dataclass, field

from quam_components.core import QuamComponent, patch_dataclass
from quam_components.components.pulses import Pulse

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10

try:
    from qm.qua import play, amp, wait, align
except ImportError:
    print("Warning: qm.qua package not found, pulses cannot be played from QuAM.")

__all__ = [
    "LocalOscillator",
    "Mixer",
    "AnalogInput",
    "PulseEmitter",
    "IQChannel",
    "SingleChannel",
]


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

    intermediate_frequency: float

    offset_I: float = 0
    offset_Q: float = 0

    correction_gain: float = 0
    correction_phase: float = 0

    controller: str = "con1"

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"mixer{self.id}"

    @property
    def frequency_drive(self):
        return self.local_oscillator.frequency + self.intermediate_frequency

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

    def play(
        self,
        pulse_name: str,
        amplitude_scale: float = None,
        duration: int = None,
        condition=None,
        chirp=None,
        truncate=None,
        timestamp_stream=None,
        continue_chirp: bool = False,
        target: str = "",
    ):
        from qm.qua._dsl import _PulseAmp

        if pulse_name not in self.pulses:
            raise KeyError(f"Pulse {pulse_name} not found in {self.name}.")

        if amplitude_scale is not None:
            if not isinstance(amplitude_scale, _PulseAmp):
                amplitude_scale = amp(amplitude_scale)
            pulse = pulse_name * amplitude_scale
        else:
            pulse = pulse_name

        # At the moment, self.name is not defined for PulseEmitter because it could
        # be a property or dataclass field in a subclass.
        # # TODO Find elegant solution for PulseEmitter.name.
        play(
            pulse=pulse,
            element=self.name,
            duration=duration,
            condition=condition,
            chirp=chirp,
            truncate=truncate,
            timestamp_stream=timestamp_stream,
            continue_chirp=continue_chirp,
            target=target,
        )

    def _config_add_pulse_waveform(self, config, pulse_label: str, pulse: Pulse):
        waveform = pulse.calculate_waveform()
        if waveform is None:
            return

        pulse_config = config["pulses"][f"{self.name}_{pulse_label}_pulse"]

        if isinstance(waveform, numbers.Number):
            wf_type = "constant"
            if isinstance(waveform, complex):
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
            waveform_name = f"{self.name}_{pulse_label}_wf"
            if suffix != "single":
                waveform_name += f"_{suffix}"

            sample_label = "sample" if wf_type == "constant" else "samples"

            config["waveforms"][waveform_name] = {
                "type": wf_type,
                sample_label: waveform,
            }
            pulse_config["waveforms"][suffix] = waveform_name

    def _config_add_pulse_integration_weights(
        self, config: dict, pulse_label: str, pulse: Pulse
    ):
        integration_weights = pulse.calculate_integration_weights()
        if not integration_weights:
            return

        pulse_config = config["pulses"][f"{self.name}_{pulse_label}_pulse"]
        pulse_config["integration_weights"] = {}
        for label, weights in integration_weights.items():
            full_label = f"{self.name}_{label}_iw"
            config["integration_weights"][full_label] = weights
            pulse_config["integration_weights"][label] = full_label

    def _config_add_pulse_digital_marker(self, config, pulse_label: str, pulse: Pulse):
        if not pulse.digital_marker:
            return

        pulse_config = config["pulses"][f"{self.name}_{pulse_label}_pulse"]
        full_label = f"{self.name}_{pulse_label}_dm"
        config["digital_waveforms"][full_label] = {"samples": pulse.digital_marker}
        pulse_config["digital_marker"] = full_label

    def apply_to_config(self, config: dict):
        for pulse_label, pulse in self.pulses.items():
            pulse_config = pulse.get_pulse_config()
            config["pulses"][f"{self.name}_{pulse_label}_pulse"] = pulse_config

            self._config_add_pulse_waveform(config, pulse_label, pulse)

            self._config_add_pulse_integration_weights(config, pulse_label, pulse)

            self._config_add_pulse_digital_marker(config, pulse_label, pulse)

    def wait(self, duration, *other_elements):
        other_elements_str = [
            element if isinstance(element, str) else str(element)
            for element in other_elements
        ]
        wait(duration, self.name, *other_elements_str)

    def align(self, *other_elements):
        assert len(other_elements)
        other_elements_str = [
            element if isinstance(element, str) else str(element)
            for element in other_elements
        ]
        align(self.name, *other_elements_str)


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
