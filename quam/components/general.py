import numbers
import numpy as np
from typing import Dict, List, Union, Tuple, Optional
from dataclasses import dataclass, field

from quam.core import QuamComponent, patch_dataclass
from quam.components.pulses import Pulse

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
    "SingleChannel",
    "IQChannel",
    "InOutIQChannel",
]


@dataclass(kw_only=True, eq=False)
class LocalOscillator(QuamComponent):
    id: Union[int, str]

    frequency: float
    power: float = None

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"lo{self.id}"


@dataclass(kw_only=True, eq=False)
class Mixer(QuamComponent):
    local_oscillator_frequency: LocalOscillator = ":../local_oscillator.frequency"
    intermediate_frequency: float = ":../intermediate_frequency"

    offset_I: float = 0
    offset_Q: float = 0

    correction_gain: float = 0
    correction_phase: float = 0

    @property
    def name(self):
        parent_id = self._get_referenced_value(":../name")
        return f"mixer_{parent_id}"

    def apply_to_config(self, config: dict):
        correction_matrix = self.IQ_imbalance(
            self.correction_gain, self.correction_phase
        )

        config["mixers"][self.name] = [
            {
                "intermediate_frequency": self.intermediate_frequency,
                "lo_frequency": self.local_oscillator_frequency,
                "correction": correction_matrix,
            }
        ]

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
        return {label: f"{self.name}${label}$pulse" for label in self.pulses}

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

        pulse_config = config["pulses"][f"{self.name}${pulse_label}$pulse"]

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
            waveform_name = f"{self.name}${pulse_label}$wf"
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

        pulse_config = config["pulses"][f"{self.name}${pulse_label}$pulse"]
        pulse_config["integration_weights"] = {}
        for label, weights in integration_weights.items():
            full_label = f"{self.name}${label}$iw"
            config["integration_weights"][full_label] = weights
            pulse_config["integration_weights"][label] = full_label

    def _config_add_pulse_digital_marker(self, config, pulse_label: str, pulse: Pulse):
        if not pulse.digital_marker:
            return

        pulse_config = config["pulses"][f"{self.name}${pulse_label}$pulse"]
        full_label = f"{self.name}${pulse_label}$dm"
        config["digital_waveforms"][full_label] = {"samples": pulse.digital_marker}
        pulse_config["digital_marker"] = full_label

    def apply_to_config(self, config: dict):
        for pulse_label, pulse in self.pulses.items():
            pulse_config = pulse.get_pulse_config()
            config["pulses"][f"{self.name}${pulse_label}$pulse"] = pulse_config

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
        if not other_elements:
            align()
        else:
            other_elements_str = [
                element if isinstance(element, str) else str(element)
                for element in other_elements
            ]
            align(self.name, *other_elements_str)


@dataclass(kw_only=True, eq=False)
class SingleChannel(PulseEmitter):
    output_port: Tuple[str, int]
    filter_fir_taps: List[float] = None
    filter_iir_taps: List[float] = None

    offset: float = 0

    @property
    def name(self) -> str:
        return f"{self.parent.name}_{self._get_parent_attr_name()}"

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)

        config["elements"][self.name] = {
            "singleInput": {
                "port": self.output_port,
            },
            "operations": self.pulse_mapping,
        }

        analog_outputs = config["controllers"][self.output_port[0]]["analog_outputs"]
        analog_output = analog_outputs[self.output_port[1]] = {"offset": self.offset}

        if self.filter_fir_taps is not None:
            output_filter = analog_output.setdefault("filter", {})
            output_filter["feedforward"] = self.filter_fir_taps

        if self.filter_iir_taps is not None:
            output_filter = analog_output.setdefault("filter", {})
            output_filter["feedback"] = self.filter_iir_taps


@dataclass(kw_only=True, eq=False)
class IQChannel(PulseEmitter):
    output_port_I: Tuple[str, int]
    output_port_Q: Tuple[str, int]

    mixer: Mixer
    local_oscillator: LocalOscillator

    intermediate_frequency: float = 0.0

    @property
    def name(self) -> str:
        return f"{self.parent.name}_{self._get_parent_attr_name()}"

    @property
    def frequency_rf(self):
        return self.local_oscillator.frequency + self.intermediate_frequency

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)

        config["elements"][self.name] = {
            "mixInputs": {
                "I": self.output_port_I,
                "Q": self.output_port_Q,
                "lo_frequency": self.local_oscillator.frequency,
                "mixer": self.mixer.name,
            },
            "intermediate_frequency": self.intermediate_frequency,
            "operations": self.pulse_mapping,
        }

        output_I = config["controllers"][self.output_port_I[0]]["analog_outputs"]
        output_I[self.output_port_I[1]] = {"offset": self.mixer.offset_I}

        output_Q = config["controllers"][self.output_port_Q[0]]["analog_outputs"]
        output_Q[self.output_port_Q[1]] = {"offset": self.mixer.offset_Q}


@dataclass(kw_only=True, eq=False)
class InOutIQChannel(IQChannel):
    time_of_flight: int = 24
    smearing: int = 0

    input_port_I: Tuple[str, int]
    input_port_Q: Tuple[str, int]

    input_offset_I: float = 0.0
    input_offset_Q: float = 0.0

    input_gain: Optional[float] = None


    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"r{self.id}"

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)

        config["elements"][self.name]["outputs"] = {
            "out1": self.input_port_I,
            "out2": self.input_port_Q,
        }
        config["elements"][self.name]["smearing"] = self.smearing
        config["elements"][self.name]["time_of_flight"] = self.time_of_flight

        input_I = config["controllers"][self.input_port_I[0]]["analog_inputs"]
        input_I[self.input_port_I[1]] = {"offset": self.input_offset_I}
        input_Q = config["controllers"][self.input_port_Q[0]]["analog_inputs"]
        input_Q[self.input_port_Q[1]] = {"offset": self.input_offset_Q}
        if self.input_gain is not None:
            input_I[self.input_port_I[1]]['gain_db'] = self.input_gain
            input_I[self.input_port_Q[1]]['gain_db'] = self.input_gain

