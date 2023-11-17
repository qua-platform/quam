from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional, Tuple, Union

from quam.components.hardware import LocalOscillator, Mixer, FrequencyConverter
from quam.components.pulses import Pulse
from quam.core import QuamComponent
from quam.utils import patch_dataclass
from quam.utils import string_reference as str_ref


try:
    from qm.qua import align, amp, play, wait
    from qm.qua._type_hinting import *
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
    """Base QuAM component for a channel, can be output, input or both.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
    """

    operations: Dict[str, Pulse] = field(default_factory=dict)

    id: Union[str, int] = None
    _default_label: ClassVar[str] = "ch"  # Used to determine name from id

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
        amplitude_scale: Union[float, AmpValuesType] = None,
        duration: QuaNumberType = None,
        condition: QuaExpressionType = None,
        chirp: ChirpType = None,
        truncate: QuaNumberType = None,
        timestamp_stream: StreamType = None,
        continue_chirp: bool = False,
        target: str = "",
    ):
        """Play a pulse on this channel.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (float, _PulseAmp): Amplitude scale of the pulse.
                Can be either a float, or qua.amp(float).
            duration (int): Duration of the pulse in units of the clock cycle (4ns).
                If not provided, the default pulse duration will be used. It is possible
                to dynamically change the duration of both constant and arbitrary
                pulses. Arbitrary pulses can only be stretched, not compressed.
            chirp (Union[(list[int], str), (int, str)]): Allows to perform
                piecewise linear sweep of the element's intermediate
                frequency in time. Input should be a tuple, with the 1st
                element being a list of rates and the second should be a
                string with the units. The units can be either: 'Hz/nsec',
                'mHz/nsec', 'uHz/nsec', 'pHz/nsec' or 'GHz/sec', 'MHz/sec',
                'KHz/sec', 'Hz/sec', 'mHz/sec'.
            truncate (Union[int, QUA variable of type int]): Allows playing
                only part of the pulse, truncating the end. If provided,
                will play only up to the given time in units of the clock
                cycle (4ns).
            condition (A logical expression to evaluate.): Will play analog
                pulse only if the condition's value is true. Any digital
                pulses associated with the operation will always play.
            timestamp_stream (Union[str, _ResultSource]): (Supported from
                QOP 2.2) Adding a `timestamp_stream` argument will save the
                time at which the operation occurred to a stream. If the
                `timestamp_stream` is a string ``label``, then the timestamp
                handle can be retrieved with
                [`qm._results.JobResults.get`][qm.results.streaming_result_fetcher.StreamingResultFetcher] with the same
                ``label``.

        Note:
            The `element` argument from `qm.qua.play()`is not needed, as it is
            automatically set to `self.name`.

        """
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

    def wait(self, duration: QuaNumberType, *other_elements: Union[str, "Channel"]):
        """Wait for the given duration on all provided elements without outputting anything.

        Duration is in units of the clock cycle (4ns)

        Args:
            duration (Union[int,QUA variable of type int]): time to wait in
                units of the clock cycle (4ns). Range: [4, $2^{31}-1$]
                in steps of 1.
            *other_elements (Union[str,sequence of str]): elements to wait on,
                in addition to this channel

        Warning:
            In case the value of this is outside the range above, unexpected results may occur.

        Note:
            The current channel element is always included in the wait operation.

        Note:
            The purpose of the `wait` operation is to add latency. In most cases, the
            latency added will be exactly the same as that specified by the QUA variable or
            the literal used. However, in some cases an additional computational latency may
            be added. If the actual wait time has significance, such as in characterization
            experiments, the actual wait time should always be verified with a simulator.
        """
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
    """QuAM component for a single (not IQ) output channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        output_port (Tuple[str, int]): Channel output port, a tuple of
            (controller_name, port).
        filter_fir_taps (List[float]): FIR filter taps for the output port.
        filter_iir_taps (List[float]): IIR filter taps for the output port.
        offset (float): DC offset for the output port.
    """

    output_port: Tuple[str, int]
    filter_fir_taps: List[float] = None
    filter_iir_taps: List[float] = None

    offset: float = 0

    def apply_to_config(self, config: dict):
        """Adds this SingleChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
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
    """QuAM component for an IQ output channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        output_port_I (Tuple[str, int]): Channel I output port, a tuple of
            (controller_name, port).
        output_port_Q (Tuple[str, int]): Channel Q output port, a tuple of
            (controller_name, port).
        mixer (Mixer): Mixer QuAM component.
        local_oscillator (LocalOscillator): Local oscillator QuAM component.
        intermediate_frequency (float): Intermediate frequency of the mixer.
    """

    output_port_I: Tuple[str, int]
    output_port_Q: Tuple[str, int]

    frequency_converter_up: FrequencyConverter
    mixer: Mixer = ":./frequency_converter_up.mixer"
    local_oscillator: LocalOscillator = ":./frequency_converter_up.local_oscillator"

    intermediate_frequency: float = 0.0

    _default_label: ClassVar[str] = "IQ"

    @property
    def rf_frequency(self):
        return self.local_oscillator.frequency + self.intermediate_frequency

    def apply_to_config(self, config: dict):
        """Adds this IQChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
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
    """QuAM component for an IQ channel with both input and output.

    An example of such a channel is a readout resonator, where you may want to
    apply a readout tone and then measure the response.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        input_port_I (Tuple[str, int]): Channel I input port, a tuple of
            (controller_name, port). Port is usually 1 or 2.
        input_port_Q (Tuple[str, int]): Channel Q input port, a tuple of
            (controller_name, port). Port is usually 1 or 2.
        output_port_I (Tuple[str, int]): Channel I output port, a tuple of
            (controller_name, port).
        output_port_Q (Tuple[str, int]): Channel Q output port, a tuple of
            (controller_name, port).
        mixer (Mixer): Mixer QuAM component for the IQ output.
        local_oscillator (LocalOscillator): Local oscillator QuAM component.
        intermediate_frequency (float): Intermediate frequency of the mixer.
    """

    local_oscillator = LocalOscillator
    frequency_converter_down: FrequencyConverter

    input_port_I: Tuple[str, int]
    input_port_Q: Tuple[str, int]

    time_of_flight: int = 24
    smearing: int = 0

    input_offset_I: float = 0.0
    input_offset_Q: float = 0.0

    input_gain: Optional[float] = None

    _default_label: ClassVar[str] = "IQ"

    def __post_init__(self):
        if self.frequency_converter_up.local_oscillator is None:
            self.frequency_converter_up.local_oscillator = "../local_oscillator"
        if self.frequency_converter_down.local_oscillator is None:
            self.frequency_converter_down.local_oscillator = "../local_oscillator"

    def apply_to_config(self, config: dict):
        """Adds this InOutIQChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        super().apply_to_config(config)

        input_ports = {"I": tuple(self.input_port_I), "Q": tuple(self.input_port_Q)}
        offsets = {"I": self.input_offset_I, "Q": self.input_offset_Q}

        # Note outputs instead of inputs because it's w.r.t. the QPU
        config["elements"][self.name]["outputs"] = {
            "out1": tuple(self.input_port_I),
            "out2": tuple(self.input_port_Q),
        }
        config["elements"][self.name]["smearing"] = self.smearing
        config["elements"][self.name]["time_of_flight"] = self.time_of_flight

        for I_or_Q in ["I", "Q"]:
            controller_name, port = input_ports[I_or_Q]
            controller = config["controllers"].setdefault(
                controller_name,
                {"analog_outputs": {}, "digital_outputs": {}, "analog_inputs": {}},
            )
            controller["analog_inputs"][port] = {"offset": offsets[I_or_Q]}

            if self.input_gain is not None:
                controller["analog_inputs"][port]["gain_db"] = self.input_gain
