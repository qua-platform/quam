import numbers
import numpy as np
from typing import Dict, List, Union, Tuple, Optional
from dataclasses import dataclass, field

from quam.core import QuamComponent, patch_dataclass
from quam.components.pulses import Pulse
from quam.utils import string_reference

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10

try:
    from qm.qua import play, amp, wait, align
except ImportError:
    print("Warning: qm.qua package not found, pulses cannot be played from QuAM.")

__all__ = [
    "LocalOscillator",
    "Mixer",
    "PulseEmitter",
    "SingleChannel",
    "IQChannel",
    "InOutIQChannel",
]


@dataclass(kw_only=True, eq=False)
class LocalOscillator(QuamComponent):
    frequency: float
    power: float = None


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
        if string_reference.is_reference(parent_id):
            raise AttributeError(f"Mixer.parent must be defined for {self}")
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
class PulseEmitter(QuamComponent):
    pulses: Dict[str, Pulse] = field(default_factory=dict)

    @property
    def pulse_mapping(self):
        return {label: pulse.pulse_name for label, pulse in self.pulses.items()}

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

    # TODO Move to ReadoutPulse
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

        controller_name, port = self.output_port
        controller = config["controllers"].setdefault(
            controller_name,
            {"analog_outputs": {}, "digital_outputs": {}, "analog_inputs": {}},
        )
        analog_output = controller["analog_outputs"][port] = {"offset": self.offset}

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
        if self.parent is None:
            raise ValueError("IQchannel.parent must be defined for it to have a name.")
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

        output_ports = [self.output_port_I, self.output_port_Q]
        offsets = [self.mixer.offset_I, self.mixer.offset_Q]
        for (controller_name, port), offset in zip(output_ports, offsets):
            controller = config["controllers"].setdefault(
                controller_name,
                {"analog_outputs": {}, "digital_outputs": {}, "analog_inputs": {}},
            )
            controller["analog_outputs"][port] = {"offset": offset}


@dataclass(kw_only=True, eq=False)
class InOutIQChannel(IQChannel):
    input_port_I: Tuple[str, int]
    input_port_Q: Tuple[str, int]

    id: Union[int, str] = ":../id"

    time_of_flight: int = 24
    smearing: int = 0

    input_offset_I: float = 0.0
    input_offset_Q: float = 0.0

    input_gain: Optional[float] = None

    @property
    def name(self):
        if string_reference.is_reference(self.id):
            raise AttributeError("InOutIQChannel.id must be defined have a parent")
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

        input_ports = [self.input_port_I, self.input_port_Q]
        offsets = [self.input_offset_I, self.input_offset_Q]
        for (controller_name, port), offset in zip(input_ports, offsets):
            controller = config["controllers"].setdefault(
                controller_name,
                {"analog_outputs": {}, "digital_outputs": {}, "analog_inputs": {}},
            )
            controller["analog_inputs"][port] = {"offset": offset}

            if self.input_gain is not None:
                controller["analog_inputs"][port]["gain_db"] = self.input_gain
