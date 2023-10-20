from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional, Tuple, Union

from quam.components.hardware import LocalOscillator, Mixer
from quam.components.pulses import Pulse
from quam.core import QuamComponent
from quam.utils import patch_dataclass
from quam.utils import string_reference as str_ref


try:
    from qm.qua import align, amp, play, wait
except ImportError:
    print("Warning: qm.qua package not found, pulses cannot be played from QuAM.")


patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10

__all__ = [
    "Channel",
    "SingleChannel",
    "IQChannel",
    "InOutIQChannel",
]


@dataclass(kw_only=True, eq=False)
class Channel(QuamComponent):
    """QuAM base component for a channel, can be output/input or both.

    Args:
        operations: A dictionary of pulses to be played on this channel.
        id: The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add _default_label
    """

    operations: Dict[str, Pulse] = field(default_factory=dict)

    id: Union[str, int] = None
    _default_label: ClassVar[str] = "ch"

    @property
    def name(self) -> str:
        cls_name = self.__class__.__name__

        if self.id is not None:
            if str_ref.is_reference(self.id):
                raise AttributeError(
                    f"{cls_name}.parent or {cls_name}.id needed to define"
                    f" {cls_name}.name"
                )
            if isinstance(self.id, str):
                return self.id
            else:
                return f"{self._default_label}{self.id}"
        if self.parent is None:
            raise AttributeError(
                f"{cls_name}.parent or {cls_name}.id needed to define {cls_name}.name"
            )
        return f"{self.parent.name}{str_ref.DELIMITER}{self._get_parent_attr_name()}"

    @property
    def pulse_mapping(self):
        return {label: pulse.pulse_name for label, pulse in self.operations.items()}

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

        if pulse_name not in self.operations:
            raise KeyError(f"Pulse {pulse_name} not found in {self.name}.")

        if amplitude_scale is not None:
            if not isinstance(amplitude_scale, _PulseAmp):
                amplitude_scale = amp(amplitude_scale)
            pulse = pulse_name * amplitude_scale
        else:
            pulse = pulse_name

        # At the moment, self.name is not defined for Channel because it could
        # be a property or dataclass field in a subclass.
        # # TODO Find elegant solution for Channel.name.
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
class SingleChannel(Channel):
    output_port: Tuple[str, int]
    filter_fir_taps: List[float] = None
    filter_iir_taps: List[float] = None

    offset: float = 0

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)

        controller_name, port = self.output_port

        config["elements"][self.name] = {
            "singleInput": {"port": (controller_name, port)},
            "operations": self.pulse_mapping,
        }

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
class IQChannel(Channel):
    output_port_I: Tuple[str, int]
    output_port_Q: Tuple[str, int]

    mixer: Mixer
    local_oscillator: LocalOscillator

    intermediate_frequency: float = 0.0

    _default_label: ClassVar[str] = "IQ"

    @property
    def frequency_rf(self):
        return self.local_oscillator.frequency + self.intermediate_frequency

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)
        output_ports = {"I": tuple(self.output_port_I), "Q": tuple(self.output_port_Q)}
        offsets = {"I": self.mixer.offset_I, "Q": self.mixer.offset_Q}

        config["elements"][self.name] = {
            "mixInputs": {
                **output_ports,
                "lo_frequency": self.local_oscillator.frequency,
                "mixer": self.mixer.name,
            },
            "intermediate_frequency": self.intermediate_frequency,
            "operations": self.pulse_mapping,
        }

        for I_or_Q in ["I", "Q"]:
            controller_name, port = output_ports[I_or_Q]
            controller = config["controllers"].setdefault(
                controller_name,
                {"analog_outputs": {}, "digital_outputs": {}, "analog_inputs": {}},
            )
            controller["analog_outputs"][port] = {"offset": offsets[I_or_Q]}


@dataclass(kw_only=True, eq=False)
class InOutIQChannel(IQChannel):
    input_port_I: Tuple[str, int]
    input_port_Q: Tuple[str, int]

    time_of_flight: int = 24
    smearing: int = 0

    input_offset_I: float = 0.0
    input_offset_Q: float = 0.0

    input_gain: Optional[float] = None

    _default_label: ClassVar[str] = "IQ"

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)

        output_ports = {"I": tuple(self.output_port_I), "Q": tuple(self.output_port_Q)}
        offsets = {"I": self.mixer.offset_I, "Q": self.mixer.offset_Q}

        config["elements"][self.name]["outputs"] = {
            "out1": tuple(self.input_port_I),
            "out2": tuple(self.input_port_Q),
        }
        config["elements"][self.name]["smearing"] = self.smearing
        config["elements"][self.name]["time_of_flight"] = self.time_of_flight

        for I_or_Q in ["I", "Q"]:
            controller_name, port = output_ports[I_or_Q]
            controller = config["controllers"].setdefault(
                controller_name,
                {"analog_outputs": {}, "digital_outputs": {}, "analog_inputs": {}},
            )
            controller["analog_inputs"][port] = {"offset": offsets[I_or_Q]}

            if self.input_gain is not None:
                controller["analog_inputs"][port]["gain_db"] = self.input_gain
