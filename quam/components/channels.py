from dataclasses import field
from typing import ClassVar, Dict, List, Optional, Tuple, Union

from quam.components.hardware import FrequencyConverter
from quam.components.pulses import Pulse, ReadoutPulse
from quam.core import QuamComponent, quam_dataclass
from quam.utils import string_reference as str_ref


try:
    from qm.qua import align, amp, play, wait, measure, dual_demod, declare, fixed
    from qm.qua._type_hinting import *
except ImportError:
    print("Warning: qm.qua package not found, pulses cannot be played from QuAM.")


__all__ = [
    "Channel",
    "SingleChannel",
    "InOutSingleChannel",
    "IQChannel",
    "InOutIQChannel",
]


@quam_dataclass
class DigitalOutputChannel(QuamComponent):
    opx_output: Tuple[str, int]
    delay: int = None
    buffer: int = None

    def apply_to_config(self, config: dict):
        controller_name, port = self.opx_output
        controller_cfg = config["controllers"].setdefault(controller_name, {})
        controller_cfg.setdefault("digital_outputs", {})
        if port not in controller_cfg["digital_outputs"]:
            controller_cfg["digital_outputs"][port] = {}


@quam_dataclass
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

    digital_channels: Dict[str, DigitalChannel] = field(default_factory=dict)

    @property
    def name(self) -> str:
        cls_name = self.__class__.__name__

        if self.id is not None:
            if str_ref.is_reference(self.id):
                raise AttributeError(
                    f"{cls_name}.name cannot be determined. "
                    f"Please either set {cls_name}.id to a string or integer, "
                    f"or {cls_name} should be an attribute of another QuAM component."
                )
            if isinstance(self.id, str):
                return self.id
            else:
                return f"{self._default_label}{self.id}"
        if self.parent is None:
            raise AttributeError(
                f"{cls_name}.name cannot be determined. "
                f"Please either set {cls_name}.id to a string or integer, "
                f"or {cls_name} should be an attribute of another QuAM component."
            )
        return f"{self.parent.name}{str_ref.DELIMITER}{self.parent.get_attr_name(self)}"

    @property
    def pulse_mapping(self):
        return {label: pulse.pulse_name for label, pulse in self.operations.items()}

    def _config_add_controller(self, config, controller_name):
        config["controllers"].setdefault(controller_name, {})
        controller_cfg = config["controllers"][controller_name]
        for key in ["analog_outputs", "digital_outputs", "analog_inputs"]:
            controller_cfg.setdefault(key, {})

        return controller_cfg

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
        validate: bool = True,
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
            validate (bool): If True (default), validate that the pulse is registered
                in Channel.operations

        Note:
            The `element` argument from `qm.qua.play()`is not needed, as it is
            automatically set to `self.name`.

        """
        from qm.qua._dsl import _PulseAmp

        if validate and pulse_name not in self.operations:
            raise KeyError(
                f"Operation '{pulse_name}' not found in channel '{self.name}'"
            )

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


@quam_dataclass
class SingleChannel(Channel):
    """QuAM component for a single (not IQ) output channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output (Tuple[str, int]): Channel output port from the OPX perspective,
            a tuple of (controller_name, port).
        filter_fir_taps (List[float]): FIR filter taps for the output port.
        filter_iir_taps (List[float]): IIR filter taps for the output port.
        opx_output_offset (float): DC offset for the output port.
        intermediate_frequency (float): Intermediate frequency of OPX output, default
            is None.
    """

    opx_output: Tuple[str, int]
    filter_fir_taps: List[float] = None
    filter_iir_taps: List[float] = None

    opx_output_offset: float = None
    intermediate_frequency: float = None

    def apply_to_config(self, config: dict):
        """Adds this SingleChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        # Add pulses & waveforms
        super().apply_to_config(config)

        if str_ref.is_reference(self.name):
            raise AttributeError(
                f"Channel {self.get_reference()} cannot be added to the config because"
                " it doesn't have a name. Either set channel.id to a string or"
                " integer, or channel should be an attribute of another QuAM component"
                " with a name."
            )

        element_config = config["elements"][self.name] = {
            "singleInput": {"port": self.opx_output},
            "operations": self.pulse_mapping,
        }
        if self.intermediate_frequency is not None:
            element_config["intermediate_frequency"] = self.intermediate_frequency

        controller_name, port = self.opx_output
        controller_cfg = self._config_add_controller(config, controller_name)
        analog_output = controller_cfg["analog_outputs"].setdefault(port, {})
        # If no offset specified, it will be added at the end of the config generation
        offset = self.opx_output_offset
        if offset is not None:
            if analog_output.get("offset", offset) != offset:
                raise ValueError(
                    f"Channel {self.name} has conflicting output offsets: "
                    f"{analog_output['offset']} and {offset}"
                )
            analog_output["offset"] = offset

        if self.filter_fir_taps is not None:
            output_filter = analog_output.setdefault("filter", {})
            output_filter["feedforward"] = self.filter_fir_taps

        if self.filter_iir_taps is not None:
            output_filter = analog_output.setdefault("filter", {})
            output_filter["feedback"] = self.filter_iir_taps


@quam_dataclass
class InOutSingleChannel(SingleChannel):
    """QuAM component for a single (not IQ) input & output channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output (Tuple[str, int]): Channel output port from OPX perspective,
            a tuple of (controller_name, port).
        opx_input (Tuple[str, int]): Channel input port from OPX perspective,
            a tuple of (controller_name, port).
        filter_fir_taps (List[float]): FIR filter taps for the output port.
        filter_iir_taps (List[float]): IIR filter taps for the output port.
        opx_output_offset (float): DC offset for the output port.
        opx_input_offset (float): DC offset for the input port.
        intermediate_frequency (float): Intermediate frequency of OPX output, default
            is None.
    """

    opx_input: Tuple[str, int]
    opx_input_offset: float = None

    time_of_flight: int = 24
    smearing: int = 0

    def apply_to_config(self, config: dict):
        """Adds this SingleChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        # Add output to config
        super().apply_to_config(config)

        # Note outputs instead of inputs because it's w.r.t. the QPU
        config["elements"][self.name]["outputs"] = {"out1": tuple(self.opx_input)}
        config["elements"][self.name]["smearing"] = self.smearing
        config["elements"][self.name]["time_of_flight"] = self.time_of_flight

        controller_name, port = self.opx_input
        controller_cfg = self._config_add_controller(config, controller_name)
        analog_input = controller_cfg["analog_inputs"].setdefault(port, {})
        offset = self.opx_input_offset
        # If no offset specified, it will be added at the end of the config generation
        if offset is not None:
            if analog_input.get("offset", offset) != offset:
                raise ValueError(
                    f"Channel {self.name} has conflicting input offsets: "
                    f"{analog_input['offset']} and {offset}"
                )
            analog_input["offset"] = offset


@quam_dataclass
class IQChannel(Channel):
    """QuAM component for an IQ output channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output_I (Tuple[str, int]): Channel I output port from the OPX perspective,
            a tuple of (controller_name, port).
        opx_output_Q (Tuple[str, int]): Channel Q output port from the OPX perspective,
            a tuple of (controller_name, port).
        opx_output_offset_I float: The offset of the I channel. Default is 0.
        opx_output_offset_Q float: The offset of the Q channel. Default is 0.
        intermediate_frequency (float): Intermediate frequency of the mixer.
        frequency_converter_up (FrequencyConverter): Frequency converter QuAM component
            for the IQ output.
    """

    opx_output_I: Tuple[str, int]
    opx_output_Q: Tuple[str, int]

    opx_output_offset_I: float = None
    opx_output_offset_Q: float = None

    frequency_converter_up: FrequencyConverter

    intermediate_frequency: float = 0.0

    _default_label: ClassVar[str] = "IQ"

    @property
    def local_oscillator(self):
        return self.frequency_converter_up.local_oscillator

    @property
    def mixer(self):
        return self.frequency_converter_up.mixer

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
        opx_outputs = {"I": tuple(self.opx_output_I), "Q": tuple(self.opx_output_Q)}
        offsets = {"I": self.opx_output_offset_I, "Q": self.opx_output_offset_Q}

        if str_ref.is_reference(self.name):
            raise AttributeError(
                f"Channel {self.get_reference()} cannot be added to the config because"
                " it doesn't have a name. Either set channel.id to a string or"
                " integer, or channel should be an attribute of another QuAM component"
                " with a name."
            )

        config["elements"][self.name] = {
            "mixInputs": {
                **opx_outputs,
            },
            "intermediate_frequency": self.intermediate_frequency,
            "operations": self.pulse_mapping,
        }
        mix_inputs = config["elements"][self.name]["mixInputs"]
        if self.mixer is not None:
            mix_inputs["mixer"] = self.mixer.name
        if self.local_oscillator is not None:
            mix_inputs["lo_frequency"] = self.local_oscillator.frequency

        for I_or_Q in ["I", "Q"]:
            controller_name, port = opx_outputs[I_or_Q]
            controller_cfg = self._config_add_controller(config, controller_name)
            analog_output = controller_cfg["analog_outputs"].setdefault(port, {})
            # If no offset specified, it will be added at the end of config generation
            if offsets[I_or_Q] is not None:
                if analog_output.get("offset", offsets[I_or_Q]) != offsets[I_or_Q]:
                    raise ValueError(
                        f"Channel {self.name} has conflicting output offsets: "
                        f"{analog_output['offset']} and {offsets[I_or_Q]}"
                    )
                analog_output["offset"] = offsets[I_or_Q]


@quam_dataclass
class InOutIQChannel(IQChannel):
    """QuAM component for an IQ channel with both input and output.

    An example of such a channel is a readout resonator, where you may want to
    apply a readout tone and then measure the response.

        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "readout") and value is a
            ReadoutPulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output_I (Tuple[str, int]): Channel I output port from the OPX perspective,
            a tuple of (controller_name, port).
        opx_output_Q (Tuple[str, int]): Channel Q output port from the OPX perspective,
            a tuple of (controller_name, port).
        opx_output_offset_I float: The offset of the I channel. Default is 0.
        opx_output_offset_Q float: The offset of the Q channel. Default is 0.
        opx_input_I (Tuple[str, int]): Channel I input port from the OPX perspective,
            a tuple of (controller_name, port).
        opx_input_Q (Tuple[str, int]): Channel Q input port from the OPX perspective,
            a tuple of (controller_name, port).
        opx_input_offset_I float: The offset of the I channel. Default is 0.
        opx_input_offset_Q float: The offset of the Q channel. Default is 0.
        intermediate_frequency (float): Intermediate frequency of the mixer.
        frequency_converter_up (FrequencyConverter): Frequency converter QuAM component
            for the IQ output.
        frequency_converter_down (Optional[FrequencyConverter]): Frequency converter
            QuAM component for the IQ input port. Only needed for the old Octave.
    """

    opx_input_I: Tuple[str, int]
    opx_input_Q: Tuple[str, int]

    time_of_flight: int = 24
    smearing: int = 0

    opx_input_offset_I: float = None
    opx_input_offset_Q: float = None

    input_gain: Optional[float] = None

    frequency_converter_down: FrequencyConverter = None

    _default_label: ClassVar[str] = "IQ"

    def apply_to_config(self, config: dict):
        """Adds this InOutIQChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        super().apply_to_config(config)

        opx_inputs = {"I": tuple(self.opx_input_I), "Q": tuple(self.opx_input_Q)}
        offsets = {"I": self.opx_input_offset_I, "Q": self.opx_input_offset_Q}

        # Note outputs instead of inputs because it's w.r.t. the QPU
        config["elements"][self.name]["outputs"] = {
            "out1": tuple(self.opx_input_I),
            "out2": tuple(self.opx_input_Q),
        }
        config["elements"][self.name]["smearing"] = self.smearing
        config["elements"][self.name]["time_of_flight"] = self.time_of_flight

        for I_or_Q in ["I", "Q"]:
            controller_name, port = opx_inputs[I_or_Q]
            controller_cfg = self._config_add_controller(config, controller_name)
            analog_input = controller_cfg["analog_inputs"].setdefault(port, {})
            # If no offset specified, it will be added at the end of config generation
            if offsets[I_or_Q] is not None:
                if analog_input.get("offset", offsets[I_or_Q]) != offsets[I_or_Q]:
                    raise ValueError(
                        f"Channel {self.name} has conflicting input offsets: "
                        f"{analog_input['offset']} and {offsets[I_or_Q]}"
                    )
                analog_input["offset"] = offsets[I_or_Q]

            if self.input_gain is not None:
                controller_cfg["analog_inputs"][port]["gain_db"] = self.input_gain

    def measure(self, pulse_name: str, I_var=None, Q_var=None, stream=None):
        """Perform a full dual demodulation measurement on this channel.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            I_var (QuaVariableType): QUA variable to store the I measurement result.
                If not provided, a new variable  will be declared
            Q_var (QuaVariableType): QUA variable to store the Q measurement result.
                If not provided, a new variable  will be declared
            stream (Optional[StreamType]): The stream to save the measurement result to.
                If not provided, the raw ADC signal will not be streamed.

        Returns:
            I_var, Q_var: The QUA variables used to store the measurement results.
                If provided as input, the same variables will be returned.
                If not provided, new variables will be declared and returned.
        """
        pulse: ReadoutPulse = self.operations[pulse_name]

        if I_var is None:
            I_var = declare(fixed)
        if Q_var is None:
            Q_var = declare(fixed)

        integration_weight_labels = list(pulse.integration_weights_mapping)
        measure(
            pulse_name,
            self.name,
            stream,
            dual_demod.full(
                iw1=integration_weight_labels[0],
                element_output1="out1",
                iw2=integration_weight_labels[1],
                element_output2="out2",
                target=I_var,
            ),
            dual_demod.full(
                iw1=integration_weight_labels[2],
                element_output1="out1",
                iw2=integration_weight_labels[0],
                element_output2="out2",
                target=Q_var,
            ),
        )
        return I_var, Q_var
