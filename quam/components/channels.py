from abc import ABC
from dataclasses import field
from typing import ClassVar, Dict, List, Optional, Sequence, Literal, Tuple, Union, Any
import warnings
from packaging.version import Version

import qm

from quam.components.hardware import BaseFrequencyConverter, Mixer, LocalOscillator
from quam.components.ports.digital_outputs import (
    DigitalOutputPort,
    OPXPlusDigitalOutputPort,
)
from quam.components.ports.analog_inputs import (
    LFAnalogInputPort,
    LFFEMAnalogInputPort,
    MWFEMAnalogInputPort,
    OPXPlusAnalogInputPort,
)
from quam.components.ports.analog_outputs import (
    LFAnalogOutputPort,
    LFFEMAnalogOutputPort,
    MWFEMAnalogOutputPort,
    OPXPlusAnalogOutputPort,
)
from quam.components.pulses import Pulse, BaseReadoutPulse
from quam.components.ports.digital_outputs import (
    FEMDigitalOutputPort,
)
from quam.core import QuamComponent, quam_dataclass
from quam.core.quam_classes import QuamDict
from quam.utils import string_reference as str_ref
from quam.utils.qua_types import (
    _PulseAmp,
    ChirpType,
    StreamType,
    ScalarInt,
    ScalarFloat,
    ScalarBool,
    QuaScalarInt,
    QuaVariableInt,
    QuaVariableFloat,
)

from qm.qua import (
    align,
    amp,
    play,
    wait,
    measure,
    declare,
    set_dc_offset,
    fixed,
    demod,
    dual_demod,
    update_frequency,
    frame_rotation,
    frame_rotation_2pi,
    time_tagging,
    reset_if_phase,
)

__all__ = [
    "Channel",
    "DigitalOutputChannel",
    "StickyChannelAddon",
    "TimeTaggingAddon",
    "SingleChannel",
    "InSingleChannel",
    "IQChannel",
    "InIQChannel",
    "InOutSingleChannel",
    "InOutIQChannel",
    "InSingleOutIQChannel",
    "InIQOutSingleChannel",
    "MWChannel",
    "InMWChannel",
    "InOutMWChannel",
]


LF_output_port_types = Union[
    LFFEMAnalogOutputPort,
    OPXPlusAnalogOutputPort,
    Tuple[str, int],
    Tuple[str, int, int],
]

LF_input_port_types = Union[
    LFFEMAnalogInputPort,
    OPXPlusAnalogInputPort,
    Tuple[str, int],
    Tuple[str, int, int],
]


@quam_dataclass
class DigitalOutputChannel(QuamComponent):
    """QUAM component for a digital output channel (signal going out of the OPX)

    Should be added to `Channel.digital_outputs` so that it's also added to the
    respective element in the QUA config.

    Args:
        opx_output (DigitalOutputPort): Channel output port from the OPX perspective,
            E.g. FEMDigitalOutputPort("con1", 1, 2)
        delay (int, optional): Delay in nanoseconds. An intrinsic negative delay of
            136 ns exists by default.
        buffer (int, optional): Digital pulses played to this element will be convolved
            with a digital pulse of value 1 with this length [ns].
        shareable (bool, optional): If True, the digital output can be shared with other
            QM instances. Default is False
        inverted (bool, optional): If True, the digital output is inverted.
            Default is False.
    ."""

    opx_output: Union[Tuple[str, int], Tuple[str, int, int], DigitalOutputPort]
    delay: int = None
    buffer: int = None

    shareable: bool = None
    inverted: bool = None

    def generate_element_config(self) -> Dict[str, int]:
        """Generates the config entry for a digital channel in the QUA config.

        This config entry goes into:
        config.elements.<element_name>.digitalInputs.<opx_output[1]>

        Returns:
            Dict[str, int]: The digital channel config entry.
                Contains "port", and optionally "delay", "buffer" if specified
        """
        if isinstance(self.opx_output, DigitalOutputPort):
            opx_output = self.opx_output.port_tuple
        else:
            opx_output = tuple(self.opx_output)

        digital_cfg: Dict[str, Any] = {"port": opx_output}
        if self.delay is not None:
            digital_cfg["delay"] = self.delay
        if self.buffer is not None:
            digital_cfg["buffer"] = self.buffer
        return digital_cfg

    def apply_to_config(self, config: dict) -> None:
        """Adds this DigitalOutputChannel to the QUA configuration.

        config.controllers.<controller_name>.digital_outputs.<port> will be updated
        with the shareable and inverted settings of this channel if specified.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        if isinstance(self.opx_output, DigitalOutputPort):
            if self.shareable is not None:
                warnings.warn(
                    f"Property {self.name}.shareable (={self.shareable}) is ignored "
                    "because it should be set in {self.name}.opx_output.shareable"
                )
            if self.inverted is not None:
                warnings.warn(
                    f"Property {self.name}.inverted (={self.inverted}) is ignored "
                    "because it should be set in {self.name}.opx_output.inverted"
                )
            return

        shareable = self.shareable if self.shareable is not None else False
        inverted = self.inverted if self.inverted is not None else False
        if len(self.opx_output) == 2:
            digital_output_port = OPXPlusDigitalOutputPort(
                *self.opx_output, shareable=shareable, inverted=inverted
            )
        else:
            digital_output_port = FEMDigitalOutputPort(
                *self.opx_output, shareable=shareable, inverted=inverted
            )
        digital_output_port.apply_to_config(config)


@quam_dataclass
class StickyChannelAddon(QuamComponent):
    """Addon to make channels sticky.

    Args:
        duration (int): The ramp to zero duration, in ns.
        enabled (bool, optional): If False, the sticky parameters are not applied.
            Default is True.
        analog (bool, optional): If False, the sticky parameters are not applied to
            analog outputs. Default is True.
        digital (bool, optional): If False, the sticky parameters are not applied to
            digital outputs. Default is True.
    """

    duration: int
    enabled: bool = True
    analog: bool = True
    digital: bool = True

    @property
    def channel(self) -> Optional["Channel"]:
        """If the parent is a channel, returns the parent, otherwise returns None."""
        if isinstance(self.parent, Channel):
            return self.parent
        else:
            return

    @property
    def config_settings(self):
        if self.channel is not None:
            return {"after": [self.channel]}

    def apply_to_config(self, config: dict) -> None:
        if self.channel is None:
            return

        if not self.enabled:
            return

        config["elements"][self.channel.name]["sticky"] = {
            "analog": self.analog,
            "digital": self.digital,
            "duration": self.duration,
        }


@quam_dataclass
class TimeTaggingAddon(QuamComponent):
    """Addon to perform time tagging on a channel.

    Args:
        signal_threshold (float, optional): The signal threshold in volts.
            If not specified, the default value is 800 / 4096 ≈ 0.195 V.
        signal_polarity (Literal["above", "below"]): The polarity of the signal
            threshold. Default is "below".
        derivative_threshold (float, optional): The derivative threshold in volts/ns.
            If not specified, the default value is 300 / 4096 ≈ 0.073 V/ns.
        derivative_polarity (Literal["above", "below"]): The polarity of the derivative
            threshold. Default is "below".

    For details see [Time Tagging](https://docs.quantum-machines.co/latest/docs/Guides/features/#time-tagging)
    """

    signal_threshold: float = 800 / 4096
    signal_polarity: Literal["above", "below"] = "below"
    derivative_threshold: float = 300 / 4096
    derivative_polarity: Literal["above", "below"] = "below"
    enabled: bool = True

    @property
    def channel(self) -> Optional["Channel"]:
        """If the parent is a channel, returns the parent, otherwise returns None."""
        if isinstance(self.parent, Channel):
            return self.parent
        else:
            return

    @property
    def config_settings(self):
        if self.channel is not None:
            return {"after": [self.channel]}

    def apply_to_config(self, config: dict) -> None:
        if self.channel is None:
            return

        if not self.enabled:
            return

        if self.signal_threshold is not None and abs(self.signal_threshold) > 1:
            raise ValueError("TimeTaggingAddon.signal_threshold must be a voltage")
        # TODO should we also check derivative threshold? What should the max value be?

        ch_cfg = config["elements"][self.channel.name]
        ch_cfg["timeTaggingParameters"] = {
            "signalThreshold": int(self.signal_threshold * 4096),
            "signalPolarity": self.signal_polarity,
            "derivativeThreshold": int(self.derivative_threshold * 4096),
            "derivativePolarity": self.derivative_polarity,
        }


@quam_dataclass
class Channel(QuamComponent, ABC):
    """Base QUAM component for a channel, can be output, input or both.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        sticky (Sticky): Optional sticky parameters for the channel, i.e. defining
            whether successive pulses are applied w.r.t the previous pulse or w.r.t 0 V.
            If not specified, this channel is not sticky.
        digital_outputs (Dict[str, DigitalOutputChannel]): A dictionary of digital
            output channels to be used on this channel. The key is the label of the
            digital output channel (e.g. "DO1") and the value is a DigitalOutputChannel.
        intermediate_frequency (float, optional): The intermediate frequency of the
            channel in Hz. If not specified, the intermediate frequency is zero.
        core (str, optional): The core to use for the channel, useful when sharing a
            core between channels. If not specified, the core is assigned automatically.
        thread (str, optional): The channel core, duplicate of 'core' argument, and
            deprecated from qm.qua >= 1.2.2.
    """

    operations: Dict[str, Pulse] = field(default_factory=dict)

    id: Union[str, int] = None
    _default_label: ClassVar[str] = "ch"  # Used to determine name from id

    digital_outputs: Dict[str, DigitalOutputChannel] = field(default_factory=dict)
    sticky: Optional[StickyChannelAddon] = None
    intermediate_frequency: Optional[float] = None

    thread: Optional[str] = None
    core: Optional[str] = None

    @property
    def name(self) -> str:
        cls_name = self.__class__.__name__

        if self.id is not None:
            if str_ref.is_reference(self.id):
                raise AttributeError(
                    f"{cls_name}.name cannot be determined. "
                    f"Please either set {cls_name}.id to a string or integer, "
                    f"or {cls_name} should be an attribute of another QUAM component."
                )
            if isinstance(self.id, str):
                return self.id
            else:
                return f"{self._default_label}{self.id}"
        if self.parent is None:
            raise AttributeError(
                f"{cls_name}.name cannot be determined. "
                f"Please either set {cls_name}.id to a string or integer, "
                f"or {cls_name} should be an attribute of another QUAM component with "
                "a name."
            )
        if isinstance(self.parent, QuamDict):
            return self.parent.get_attr_name(self)
        if not hasattr(self.parent, "name"):
            raise AttributeError(
                f"{cls_name}.name cannot be determined. "
                f"Please either set {cls_name}.id to a string or integer, "
                f"or {cls_name} should be an attribute of another QUAM component with "
                "a name."
            )
        return f"{self.parent.name}{str_ref.DELIMITER}{self.parent.get_attr_name(self)}"

    @property
    def pulse_mapping(self):
        return {label: pulse.pulse_name for label, pulse in self.operations.items()}

    def play(
        self,
        pulse_name: str,
        amplitude_scale: Union[ScalarFloat, Sequence[ScalarFloat]] = None,
        duration: ScalarInt = None,
        condition: ScalarBool = None,
        chirp: ChirpType = None,
        truncate: ScalarInt = None,
        timestamp_stream: StreamType = None,
        continue_chirp: bool = False,
        target: str = "",
        validate: bool = True,
    ):
        """Play a pulse on this channel.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (Union[ScalarFloat, Sequence[ScalarFloat]]): Amplitude scale
                of the pulse. Can be either a float, qua.amp(float), or a list of
                floats.
            duration (Scalar[int]): Duration of the pulse in units of the
                clock cycle (4ns). If not provided, the default pulse duration will be
                used. It is possible to dynamically change the duration of both constant
                and arbitrary pulses. Arbitrary pulses can only be stretched, not
                compressed
            chirp (Union[(list[int], str), (int, str)]): Allows to perform
                piecewise linear sweep of the element's intermediate
                frequency in time. Input should be a tuple, with the 1st
                element being a list of rates and the second should be a
                string with the units. The units can be either: 'Hz/nsec',
                'mHz/nsec', 'uHz/nsec', 'pHz/nsec' or 'GHz/sec', 'MHz/sec',
                'KHz/sec', 'Hz/sec', 'mHz/sec'.
            truncate (Scalar[int]): Allows playing
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
                `qm._results.JobResults.get` with the same ``label``.
            validate (bool): If True (default), validate that the pulse is registered
                in Channel.operations

        Note:
            The `element` argument from `qm.qua.play()`is not needed, as it is
            automatically set to `self.name`.

        """
        if validate and pulse_name not in self.operations:
            raise KeyError(
                f"Operation '{pulse_name}' not found in channel '{self.name}'"
            )

        if amplitude_scale is not None:
            if isinstance(amplitude_scale, _PulseAmp):
                warnings.warn(
                    "Setting amplitude_scale=amp(...) is deprecated, please "
                    "pass a float or list of floats instead",
                    DeprecationWarning,
                )
            elif isinstance(amplitude_scale, Sequence):
                amplitude_scale = amp(*amplitude_scale)
            else:
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

    def wait(self, duration: ScalarInt, *other_elements: Union[str, "Channel"]):
        """Wait for the given duration on all provided elements without outputting anything.

        Duration is in units of the clock cycle (4ns)

        Args:
            duration (Scalar[int]): time to wait in units of the clock cycle
                (4ns). Range: [4, $2^{31}-1$] in steps of 1.
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

    def update_frequency(
        self,
        new_frequency: ScalarInt,
        units: str = "Hz",
        keep_phase: bool = False,
    ):
        """Dynamically update the frequency of the associated oscillator.

        This changes the frequency from the value defined in the channel.

        The behavior of the phase (continuous vs. coherent) is controlled by the
        ``keep_phase`` parameter and is discussed in the documentation.

        Args:
            new_frequency (Scalar[int]): The new frequency value to set
                in units set by ``units`` parameter. In steps of 1.
            units (str): units of new frequency. Useful when sub-Hz
                precision is required. Allowed units are "Hz", "mHz", "uHz",
                "nHz", "pHz"
            keep_phase (bool): Determine whether phase will be continuous
                through the change (if ``True``) or it will be coherent,
                only the frequency will change (if ``False``).

        Example:
            ```python
            with program() as prog:
                update_frequency("q1", 4e6) # will set the frequency to 4 MHz

                ### Example for sub-Hz resolution
                # will set the frequency to 100 Hz (due to casting to int)
                update_frequency("q1", 100.7)

                # will set the frequency to 100.7 Hz
                update_frequency("q1", 100700, units='mHz')
            ```
        """
        update_frequency(self.name, new_frequency, units, keep_phase)

    def reset_if_phase(self):
        r"""
        Resets the intermediate frequency phase of the oscillator, setting the phase of
        the next pulse to absolute zero.
        This sets the phase of the currently playing intermediate frequency
        to the value it had at the beginning of the program (t=0).

        Note:
        - The phase will only be set to zero when the next play or align command is
          executed on the element.
        - Reset phase will only reset the phase of the intermediate frequency
          (:math:`\\omega_{IF}`) currently in use.
        """
        reset_if_phase(self.name)

    def frame_rotation(self, angle: ScalarFloat):
        r"""Shift the phase of the channel element's oscillator by the given angle.

        This is typically used for virtual z-rotations.

        Note:
            The fixed point format of QUA variables of type fixed is 4.28, meaning the
            phase must be between $-8$ and $8-2^{28}$. Otherwise the phase value will be
            invalid. It is therefore better to use `frame_rotation_2pi()` which avoids
            this issue.

        Note:
            The phase is accumulated with a resolution of 16 bit.
            Therefore, *N* changes to the phase can result in a phase (and amplitude)
            inaccuracy of about :math:`N \cdot 2^{-16}`. To null out this accumulated
            error, it is recommended to use `reset_frame(el)` from time to time.

        Args:
            angle (Scalar[float]): The angle to add to the current
                phase (in radians)
            *elements (str): a single element whose oscillator's phase will
                be shifted. multiple elements can be given, in which case
                all of their oscillators' phases will be shifted

        """
        frame_rotation(angle, self.name)

    def frame_rotation_2pi(self, angle: ScalarFloat):
        r"""Shift the phase of the oscillator associated with an element by the given
        angle in units of 2pi radians.

        This is typically used for virtual z-rotations.

        Note:
            Unlike the case of frame_rotation(), this method performs the 2-pi radian
            wrap around of the angle automatically.

        Note:
            The phase is accumulated with a resolution of 16 bit.
            Therefore, *N* changes to the phase can result in a phase inaccuracy of
            about :math:`N \cdot 2^{-16}`. To null out this accumulated error, it is
            recommended to use `reset_frame(el)` from time to time.

        Args:
            angle (Scalar[float]): The angle to add to the current
                phase (in $2\pi$ radians)
        """
        frame_rotation_2pi(angle, self.name)

    def _config_add_digital_outputs(self, config: Dict[str, dict]) -> None:
        """Adds the digital outputs to the QUA config.

        config.elements.<element_name>.digitalInputs will be updated with the digital
        outputs of this channel.

        Note that the digital outputs are added separately to the controller config in
        `DigitalOutputChannel.apply_to_config`.

        Args:
            config (dict): The QUA config that's in the process of being generated.
        """
        if not self.digital_outputs:
            return

        element_config = config["elements"][self.name]
        element_config.setdefault("digitalInputs", {})

        for name, digital_output in self.digital_outputs.items():
            digital_cfg = digital_output.generate_element_config()
            element_config["digitalInputs"][name] = digital_cfg

    def apply_to_config(self, config: Dict[str, dict]) -> None:
        """Adds this Channel to the QUA configuration.

        config.elements.<element_name> will be created, and the operations are added.

        Args:
            config (dict): The QUA config that's in the process of being generated.

        Raises:
            ValueError: If the channel already exists in the config.
        """
        if self.name in config["elements"]:
            raise ValueError(
                f"Cannot add channel '{self.name}' to the config because it already "
                f"exists. Existing entry: {config['elements'][self.name]}"
            )
        config["elements"][self.name] = {"operations": self.pulse_mapping}
        element_config = config["elements"][self.name]

        if self.intermediate_frequency is not None:
            element_config["intermediate_frequency"] = self.intermediate_frequency

        try:
            qua_below_1_2_2 = Version(qm.__version__) <= Version("1.2.1")
        except ImportError:
            warnings.warn(
                "Unable to to determine qm package version, assuming < 1.2.2. "
            )
            qua_below_1_2_2 = True

        if self.core is not None and self.thread is not None:
            warnings.warn(
                "The 'thread' and 'core' arguments are mutually exclusive. "
                "Using 'core' instead."
            )
            core = self.core
        elif self.thread is not None:
            if not qua_below_1_2_2:
                warnings.warn(
                    "The 'thread' element argument is deprecated from qm.qua >= 1.2.2. "
                    "Use 'core' instead."
                )
            core = self.thread
        else:
            core = self.core

        if core is not None:
            if qua_below_1_2_2:
                element_config["thread"] = core
            else:
                element_config["core"] = core

        self._config_add_digital_outputs(config)


@quam_dataclass
class SingleChannel(Channel):
    """QUAM component for a single (not IQ) output channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output (LF_output_port_types): Channel output port from the OPX perspective,
            E.g. LFFEMAnalogOutputPort("con1", 1, 2)
        filter_fir_taps (List[float]): FIR filter taps for the output port.
        filter_iir_taps (List[float]): IIR filter taps for the output port.
        opx_output_offset (float): DC offset for the output port.
        intermediate_frequency (float): Intermediate frequency of OPX output, default
            is None.
    """

    opx_output: LF_output_port_types
    filter_fir_taps: List[float] = None
    filter_iir_taps: List[float] = None

    opx_output_offset: float = None

    def set_dc_offset(self, offset: ScalarFloat):
        """Set the DC offset of an element's input to the given value.
        This value will remain the DC offset until changed or until the Quantum Machine
        is closed.

        Args:
            offset (Scalar[float]): The DC offset to set the input to.
                This is limited by the OPX output voltage range.
        """
        set_dc_offset(element=self.name, element_input="single", offset=offset)

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
                " integer, or channel should be an attribute of another QUAM component"
                " with a name."
            )

        element_config = config["elements"][self.name]

        filter_fir_taps = self.filter_fir_taps
        if filter_fir_taps is not None:
            warnings.warn(
                "SingleChannel.filter_fir_taps have moved to the analog output port "
                "property 'feedforward_filter'. Please update your QUAM state.",
                DeprecationWarning,
            )
            filter_fir_taps = list(filter_fir_taps)
        filter_iir_taps = self.filter_iir_taps
        if filter_iir_taps is not None:
            warnings.warn(
                "SingleChannel.filter_iir_taps have moved to the analog output port "
                "property 'feedback_filter' (OPX+), or 'exponential_filter' and "
                "'high_pass_filter' (LF-FEM). Please update your QUAM state.",
                DeprecationWarning,
            )
            filter_iir_taps = list(filter_iir_taps)

        if isinstance(self.opx_output, LFAnalogOutputPort):
            opx_port = self.opx_output
        elif len(self.opx_output) == 2:
            opx_port = OPXPlusAnalogOutputPort(
                *self.opx_output,
                offset=self.opx_output_offset,
                feedforward_filter=filter_fir_taps,
                feedback_filter=filter_iir_taps,
            )
            opx_port.apply_to_config(config)
        else:
            opx_port = LFFEMAnalogOutputPort(
                *self.opx_output,
                offset=self.opx_output_offset,
                feedforward_filter=filter_fir_taps,
                feedback_filter=filter_iir_taps,
            )
            opx_port.apply_to_config(config)

        element_config["singleInput"] = {"port": opx_port.port_tuple}


@quam_dataclass
class InSingleChannel(Channel):
    """QUAM component for a single (not IQ) input channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_input (LF_input_port_types): Channel input port from OPX perspective,
            E.g. LFFEMAnalogInputPort("con1", 1, 2)
        opx_input_offset (float): DC offset for the input port.
        intermediate_frequency (float): Intermediate frequency of OPX input,
            default is None.
        time_of_flight (int): Round-trip signal duration in nanoseconds.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing.
    """

    opx_input: LF_input_port_types
    opx_input_offset: float = None

    time_of_flight: int = 140
    smearing: int = 0

    time_tagging: Optional[TimeTaggingAddon] = None

    def apply_to_config(self, config: dict):
        """Adds this InSingleChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        # Add output to config
        super().apply_to_config(config)

        # Note outputs instead of inputs because it's w.r.t. the QPU
        element_config = config["elements"][self.name]
        element_config["smearing"] = self.smearing
        element_config["time_of_flight"] = self.time_of_flight

        if isinstance(self.opx_input, LFAnalogInputPort):
            opx_port = self.opx_input
        elif len(self.opx_input) == 2:
            opx_port = OPXPlusAnalogInputPort(
                *self.opx_input, offset=self.opx_input_offset
            )
            opx_port.apply_to_config(config)
        else:
            opx_port = LFFEMAnalogInputPort(
                *self.opx_input, offset=self.opx_input_offset
            )
            opx_port.apply_to_config(config)

        element_config["outputs"] = {"out1": opx_port.port_tuple}

    def measure(
        self,
        pulse_name: str,
        amplitude_scale: Union[ScalarFloat, Sequence[ScalarFloat]] = None,
        qua_vars: Tuple[QuaVariableFloat, ...] = None,
        stream=None,
    ) -> Tuple[QuaVariableFloat, QuaVariableFloat]:
        """Perform a full demodulation measurement on this channel.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (Union[ScalarFloat, Sequence[ScalarFloat]]): Amplitude
                scale of the pulse. Can be either a float, qua.amp(float), or a list of
                floats.
            qua_vars (Tuple[QuaVariable[float], ...], optional): Two QUA
                variables to store the I, Q measurement results.
                If not provided, new variables will be declared and returned.
            stream (Optional[StreamType]): The stream to save the measurement result to.
                If not provided, the raw ADC signal will not be streamed.

        Returns:
            I, Q: The QUA variables used to store the measurement results.
                If provided as input, the same variables will be returned.
                If not provided, new variables will be declared and returned.

        Raises:
            ValueError: If `qua_vars` is provided and is not a tuple of two QUA
                variables.
        """

        pulse: BaseReadoutPulse = self.operations[pulse_name]

        if qua_vars is not None:
            if not isinstance(qua_vars, Sequence) or len(qua_vars) != 2:
                raise ValueError(
                    f"InOutSingleChannel.measure received kwarg 'qua_vars' "
                    f"which is not a tuple of two QUA variables. Received {qua_vars=}"
                )
        else:
            qua_vars = [declare(fixed) for _ in range(2)]

        if amplitude_scale is not None:
            if not isinstance(amplitude_scale, _PulseAmp):
                amplitude_scale = amp(amplitude_scale)
            pulse_name *= amplitude_scale

        integration_weight_labels = list(pulse.integration_weights_mapping)
        measure(
            pulse_name,
            self.name,
            stream,
            demod.full(integration_weight_labels[0], qua_vars[0], "out1"),
            demod.full(integration_weight_labels[1], qua_vars[1], "out1"),
        )
        return tuple(qua_vars)

    def measure_accumulated(
        self,
        pulse_name: str,
        amplitude_scale: Union[ScalarFloat, Sequence[ScalarFloat]] = None,
        num_segments: int = None,
        segment_length: int = None,
        qua_vars: Tuple[QuaVariableFloat, ...] = None,
        stream=None,
    ) -> Tuple[QuaVariableFloat, QuaVariableFloat]:
        """Perform an accumulated demodulation measurement on this channel.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (Union[ScalarFloat, Sequence[ScalarFloat]]): Amplitude
                scale of the pulse. Can be either a float, qua.amp(float), or a list of
                floats.
            num_segments (int): The number of segments to accumulate.
                Should either specify this or `segment_length`.
            segment_length (int): The length of the segment to accumulate.
                Should either specify this or `num_segments`.
            qua_vars (Tuple[QuaVariableFloat, ...], optional): Two QUA
                variables to store the I, Q measurement results.
                If not provided, new variables will be declared and returned.
            stream (Optional[StreamType]): The stream to save the measurement result to.
                If not provided, the raw ADC signal will not be streamed.

        Returns:
            I, Q: The QUA variables used to store the measurement results.
                If provided as input, the same variables will be returned.
                If not provided, new variables will be declared and returned.

        Raises:
            ValueError: If both `num_segments` and `segment_length` are provided, or if
                neither are provided.
            ValueError: If `qua_vars` is provided and is not a tuple of two QUA
                variables.
        """
        pulse: BaseReadoutPulse = self.operations[pulse_name]

        if num_segments is None and segment_length is None:
            raise ValueError(
                "InOutSingleChannel.measure_accumulated requires either 'segment_length' "
                "or 'num_segments' to be provided."
            )
        elif num_segments is not None and segment_length is not None:
            raise ValueError(
                "InOutSingleChannel.measure_accumulated received both 'segment_length' "
                "and 'num_segments'. Please provide only one."
            )
        elif num_segments is None:
            num_segments = int(pulse.length / (4 * segment_length))  # Number of slices
        elif segment_length is None:
            segment_length = int(pulse.length / (4 * num_segments))

        if qua_vars is not None:
            if not isinstance(qua_vars, Sequence) or len(qua_vars) != 2:
                raise ValueError(
                    f"InOutSingleChannel.measure_accumulated received kwarg 'qua_vars' "
                    f"which is not a tuple of two QUA variables. Received {qua_vars=}"
                )
        else:
            qua_vars = [declare(fixed, size=num_segments) for _ in range(2)]

        if amplitude_scale is not None:
            if not isinstance(amplitude_scale, _PulseAmp):
                amplitude_scale = amp(amplitude_scale)
            pulse_name *= amplitude_scale

        integration_weight_labels = list(pulse.integration_weights_mapping)
        measure(
            pulse_name,
            self.name,
            stream,
            demod.accumulated(
                integration_weight_labels[0], qua_vars[0], segment_length, "out1"
            ),
            demod.accumulated(
                integration_weight_labels[1], qua_vars[1], segment_length, "out1"
            ),
        )
        return tuple(qua_vars)

    def measure_sliced(
        self,
        pulse_name: str,
        amplitude_scale: Union[ScalarFloat, Sequence[ScalarFloat]] = None,
        num_segments: int = None,
        segment_length: int = None,
        qua_vars: Tuple[QuaVariableFloat, ...] = None,
        stream=None,
    ) -> Tuple[QuaVariableFloat, QuaVariableFloat]:
        """Perform an accumulated demodulation measurement on this channel.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (Union[ScalarFloat, Sequence[ScalarFloat]]): Amplitude
                scale of the pulse. Can be either a float, qua.amp(float), or a list of
                floats.
            num_segments (int): The number of segments to accumulate.
                Should either specify this or `segment_length`.
            segment_length (int): The length of the segment to accumulate.
                Should either specify this or `num_segments`.
            qua_vars (Tuple[QuaVariableFloat, ...], optional): Two QUA
                variables to store the I, Q measurement results.
                If not provided, new variables will be declared and returned.
            stream (Optional[StreamType]): The stream to save the measurement result to.
                If not provided, the raw ADC signal will not be streamed.

        Returns:
            I, Q: The QUA variables used to store the measurement results.
                If provided as input, the same variables will be returned.
                If not provided, new variables will be declared and returned.

        Raises:
            ValueError: If both `num_segments` and `segment_length` are provided, or if
                neither are provided.
            ValueError: If `qua_vars` is provided and is not a tuple of two QUA
                variables.
        """
        pulse: BaseReadoutPulse = self.operations[pulse_name]

        if num_segments is None and segment_length is None:
            raise ValueError(
                "InOutSingleChannel.measure_sliced requires either 'segment_length' "
                "or 'num_segments' to be provided."
            )
        elif num_segments is not None and segment_length is not None:
            raise ValueError(
                "InOutSingleChannel.measure_sliced received both 'segment_length' "
                "and 'num_segments'. Please provide only one."
            )
        elif num_segments is None:
            num_segments = int(pulse.length / (4 * segment_length))  # Number of slices
        elif segment_length is None:
            segment_length = int(pulse.length / (4 * num_segments))

        if qua_vars is not None:
            if not isinstance(qua_vars, Sequence) or len(qua_vars) != 2:
                raise ValueError(
                    f"InOutSingleChannel.measure_sliced received kwarg 'qua_vars' "
                    f"which is not a tuple of two QUA variables. Received {qua_vars=}"
                )
        else:
            qua_vars = [declare(fixed, size=num_segments) for _ in range(2)]

        if amplitude_scale is not None:
            if not isinstance(amplitude_scale, _PulseAmp):
                amplitude_scale = amp(amplitude_scale)
            pulse_name *= amplitude_scale

        integration_weight_labels = list(pulse.integration_weights_mapping)
        measure(
            pulse_name,
            self.name,
            stream,
            demod.sliced(
                integration_weight_labels[0], qua_vars[0], segment_length, "out1"
            ),
            demod.sliced(
                integration_weight_labels[1], qua_vars[1], segment_length, "out1"
            ),
        )
        return tuple(qua_vars)

    def measure_time_tagging(
        self,
        pulse_name: str,
        size: int,
        max_time: int,
        qua_vars: Optional[Tuple[QuaVariableInt, QuaScalarInt]] = None,
        stream: Optional[StreamType] = None,
        mode: Literal["analog", "high_res", "digital"] = "analog",
    ) -> Tuple[QuaVariableInt, QuaScalarInt]:
        """Perform a time tagging measurement on this channel.

        For details see https://docs.quantum-machines.co/latest/docs/Guides/features/#time-tagging

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            size (int): The size of the QUA array to store the times of the detected
                pulses. Ignored if `qua_vars` is provided.
            max_time (int): The maximum time to search for pulses.
            qua_vars (Tuple[QuaVariableInt, QuaScalarInt], optional): QUA variables
                to store the times and counts of the detected pulses. If not provided,
                new variables will be declared and returned.
            stream (Optional[StreamType]): The stream to save the measurement result to.
                If not provided, the raw ADC signal will not be streamed.
            mode (Literal["analog", "high_res", "digital"]): The time tagging mode.

        Returns:
            times (QuaVariable[Any]): The QUA variable to store the times of the detected
                pulses.
            counts (QuaScalar[int]): The number of detected pulses.

        Example:
            ```python
            times, counts = channel.measure_time_tagging("readout", size=1000, max_time=1000)
            ```
        """
        if mode == "analog":
            time_tagging_func = time_tagging.analog
        elif mode == "high_res":
            time_tagging_func = time_tagging.high_res
        elif mode == "digital":
            time_tagging_func = time_tagging.digital
        else:
            raise ValueError(f"Invalid time tagging mode: {mode}")

        if qua_vars is None:
            times = declare(int, size=size)
            counts = declare(int)
        else:
            times, counts = qua_vars

        measure(
            pulse_name,
            self.name,
            stream,
            time_tagging_func(target=times, max_time=max_time, targetLen=counts),
        )
        return times, counts


@quam_dataclass
class _OutComplexChannel(Channel, ABC):
    """Base class for IQ and MW output channels."""

    LO_frequency: float
    RF_frequency: float

    @property
    def inferred_RF_frequency(self) -> float:
        """Inferred RF frequency by adding LO and IF

        Can be used by having reference `RF_frequency = "#./inferred_RF_frequency"`
        Returns:
            self.LO_frequency + self.intermediate_frequency
        """
        name = getattr(self, "name", self.__class__.__name__)
        if not isinstance(self.LO_frequency, (float, int)):
            raise AttributeError(
                f"Error inferring RF frequency for channel {name}: "
                f"LO_frequency is not a number: {self.LO_frequency}"
            )
        if not isinstance(self.intermediate_frequency, (float, int)):
            raise AttributeError(
                f"Error inferring RF frequency for channel {name}: "
                f"intermediate_frequency is not a number: {self.intermediate_frequency}"
            )
        return self.LO_frequency + self.intermediate_frequency

    @property
    def inferred_intermediate_frequency(self) -> float:
        """Inferred intermediate frequency by subtracting LO from RF

        Can be used by having reference
        `intermediate_frequency = "#./inferred_intermediate_frequency"`

        Returns:
            self.RF_frequency - self.LO_frequency
        """
        name = getattr(self, "name", self.__class__.__name__)
        if not isinstance(self.LO_frequency, (float, int)):
            raise AttributeError(
                f"Error inferring intermediate frequency for channel {name}: "
                f"LO_frequency is not a number: {self.LO_frequency}"
            )
        if not isinstance(self.RF_frequency, (float, int)):
            raise AttributeError(
                f"Error inferring intermediate frequency for channel {name}: "
                f"RF_frequency is not a number: {self.RF_frequency}"
            )
        return self.RF_frequency - self.LO_frequency

    @property
    def inferred_LO_frequency(self) -> float:
        """Inferred LO frequency by subtracting IF from RF

        Can be used by having reference `LO_frequency = "#./inferred_LO_frequency"`

        Returns:
            self.RF_frequency - self.intermediate_frequency
        """
        name = getattr(self, "name", self.__class__.__name__)
        if not isinstance(self.RF_frequency, (float, int)):
            raise AttributeError(
                f"Error inferring LO frequency for channel {name}: "
                f"RF_frequency is not a number: {self.RF_frequency}"
            )
        if not isinstance(self.intermediate_frequency, (float, int)):
            raise AttributeError(
                f"Error inferring LO frequency for channel {name}: "
                f"intermediate_frequency is not a number: {self.intermediate_frequency}"
            )
        return self.RF_frequency - self.intermediate_frequency


@quam_dataclass
class IQChannel(_OutComplexChannel):
    """QUAM component for an IQ output channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output_I (LF_output_port_types): Channel I output port from the OPX
            perspective, E.g. LFFEMAnalogOutputPort("con1", 1, 1)
        opx_output_Q (LF_output_port_types): Channel Q output port from the OPX
            perspective, E.g. LFFEMAnalogOutputPort("con1", 1, 2)
        opx_output_offset_I (float): The offset of the I channel. Default is 0.
        opx_output_offset_Q (float): The offset of the Q channel. Default is 0.
        intermediate_frequency (float): Intermediate frequency of the mixer.
            Default is 0.0
        LO_frequency (float): Local oscillator frequency. Default is the LO frequency
            of the frequency converter up component.
        RF_frequency (float): RF frequency of the mixer. By default, the RF frequency
            is inferred by adding the LO frequency and the intermediate frequency.
        frequency_converter_up (FrequencyConverter): Frequency converter QUAM component
            for the IQ output.
    """

    opx_output_I: LF_output_port_types
    opx_output_Q: LF_output_port_types

    opx_output_offset_I: float = None
    opx_output_offset_Q: float = None

    frequency_converter_up: BaseFrequencyConverter

    LO_frequency: float = "#./frequency_converter_up/LO_frequency"
    RF_frequency: float = "#./inferred_RF_frequency"

    _default_label: ClassVar[str] = "IQ"

    @property
    def local_oscillator(self) -> Optional[LocalOscillator]:
        return getattr(self.frequency_converter_up, "local_oscillator", None)

    @property
    def mixer(self) -> Optional[Mixer]:
        return getattr(self.frequency_converter_up, "mixer", None)

    @property
    def rf_frequency(self):
        warnings.warn(
            "rf_frequency is deprecated, use RF_frequency instead", DeprecationWarning
        )
        return self.frequency_converter_up.LO_frequency + self.intermediate_frequency

    def set_dc_offset(self, offset: ScalarFloat, element_input: Literal["I", "Q"]):
        """Set the DC offset of an element's input to the given value.
        This value will remain the DC offset until changed or until the Quantum Machine
        is closed.

        Args:
            offset (Scalar[float]): The DC offset to set the input to.
                This is limited by the OPX output voltage range.
            element_input (Literal["I", "Q"]): The element input to set the offset for.

        Raises:
            ValueError: If element_input is not "I" or "Q"
        """
        if element_input not in ["I", "Q"]:
            raise ValueError(
                f"element_input should be either 'I' or 'Q', got {element_input}"
            )
        set_dc_offset(element=self.name, element_input=element_input, offset=offset)

    def apply_to_config(self, config: dict):
        """Adds this IQChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        # Add pulses & waveforms
        super().apply_to_config(config)

        if str_ref.is_reference(self.name):
            raise AttributeError(
                f"Channel {self.get_reference()} cannot be added to the config because"
                " it doesn't have a name. Either set channel.id to a string or"
                " integer, or channel should be an attribute of another QUAM component"
                " with a name."
            )

        element_config = config["elements"][self.name]

        from quam.components.octave import OctaveUpConverter

        if isinstance(self.frequency_converter_up, OctaveUpConverter):
            octave = self.frequency_converter_up.octave
            if octave is None:
                raise ValueError(
                    f"Error generating config: channel {self.name} has an "
                    f"OctaveUpConverter (id={self.frequency_converter_up.id}) without "
                    "an attached Octave"
                )
            element_config["RF_inputs"] = {
                "port": (octave.name, self.frequency_converter_up.id)
            }
        elif str_ref.is_reference(self.frequency_converter_up):
            raise ValueError(
                f"Error generating config: channel {self.name} could not determine "
                f'"frequency_converter_up", it seems to point to a non-existent '
                f"reference: {self.frequency_converter_up}"
            )
        else:
            element_config["mixInputs"] = {}  # To be filled in next section
            if self.mixer is not None:
                element_config["mixInputs"]["mixer"] = self.mixer.name
            if self.local_oscillator is not None:
                element_config["mixInputs"]["lo_frequency"] = (
                    self.local_oscillator.frequency
                )

        opx_outputs = [self.opx_output_I, self.opx_output_Q]
        offsets = [self.opx_output_offset_I, self.opx_output_offset_Q]
        for I_or_Q, opx_output, offset in zip("IQ", opx_outputs, offsets):
            if isinstance(opx_output, LFAnalogOutputPort):
                opx_port = opx_output
            elif len(opx_output) == 2:
                opx_port = OPXPlusAnalogOutputPort(*opx_output, offset=offset)
                opx_port.apply_to_config(config)
            else:
                opx_port = LFFEMAnalogOutputPort(*opx_output, offset=offset)
                opx_port.apply_to_config(config)

            if "mixInputs" in element_config:
                element_config["mixInputs"][I_or_Q] = opx_port.port_tuple


@quam_dataclass
class _InComplexChannel(Channel, ABC):
    """A specialized channel class for performing complex demodulation measurements.

    This class extends the basic `Channel` class and provides functionality
    for performing full dual demodulation measurements on a channel. It allows
    for the measurement of both in-phase (I) and quadrature (Q) components of
    a signal, which are essential for characterizing quantum signals.

    This class is used for both input IQ channels on low-frequency analog inputs and for
    MW inputs in the MW FEM.
    """

    def measure(
        self,
        pulse_name: str,
        amplitude_scale: Union[ScalarFloat, Sequence[ScalarFloat]] = None,
        qua_vars: Tuple[QuaVariableFloat, QuaVariableFloat] = None,
        stream=None,
    ) -> Tuple[QuaVariableFloat, QuaVariableFloat]:
        """Perform a full dual demodulation measurement on this channel.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (Union[ScalarFloat, Sequence[ScalarFloat]]): Amplitude
                scale of the pulse. Can be either a float, qua.amp(float), or a list of
                floats.
            qua_vars (Tuple[QuaVariable[float], QuaVariable[float]], optional): Two QUA
                variables to store the I and Q measurement results. If not provided,
                new variables will be declared and returned.
            stream (Optional[StreamType]): The stream to save the measurement result to.
                If not provided, the raw ADC signal will not be streamed.

        Returns:
            I, Q: The QUA variables used to store the measurement results.
                If provided as input, the same variables will be returned.
                If not provided, new variables will be declared and returned.
        """
        pulse: BaseReadoutPulse = self.operations[pulse_name]

        if qua_vars is not None:
            if not isinstance(qua_vars, Sequence) or len(qua_vars) != 2:
                raise ValueError(
                    f"InOutIQChannel.measure received kwarg 'qua_vars' which is not a "
                    f"tuple of two QUA variables. Received {qua_vars=}"
                )
        else:
            qua_vars = [declare(fixed) for _ in range(2)]

        if amplitude_scale is not None:
            if not isinstance(amplitude_scale, _PulseAmp):
                amplitude_scale = amp(amplitude_scale)
            pulse_name *= amplitude_scale

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
                target=qua_vars[0],
            ),
            dual_demod.full(
                iw1=integration_weight_labels[2],
                element_output1="out1",
                iw2=integration_weight_labels[0],
                element_output2="out2",
                target=qua_vars[1],
            ),
        )
        return tuple(qua_vars)

    def measure_accumulated(
        self,
        pulse_name: str,
        amplitude_scale: Optional[Union[ScalarFloat, Sequence[ScalarFloat]]] = None,
        num_segments: Optional[int] = None,
        segment_length: Optional[int] = None,
        qua_vars: Optional[Tuple[QuaVariableFloat, ...]] = None,
        stream=None,
    ) -> Tuple[QuaVariableFloat, QuaVariableFloat, QuaVariableFloat, QuaVariableFloat]:
        """Perform an accumulated dual demodulation measurement on this channel.

        Instead of two QUA variables (I and Q), this method returns four variables
        (II, IQ, QI, QQ)

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (Union[ScalarFloat, Sequence[ScalarFloat]]): Amplitude
                scale of the pulse. Can be either a float, qua.amp(float), or a list of
                floats.
            num_segments (int): The number of segments to accumulate.
                Should either specify this or `segment_length`.
            segment_length (int): The length of the segment to accumulate the
                measurement.
                Should either specify this or `num_segments`.
            qua_vars (Tuple[QuaVariableFloat, ...], optional): Four QUA
                variables to store the II, IQ, QI, QQ measurement results.
                If not provided, new variables will be declared and returned.
            stream (Optional[StreamType]): The stream to save the measurement result to.
                If not provided, the raw ADC signal will not be streamed.

        Returns:
            II, IQ, QI, QQ: The QUA variables used to store the measurement results.
                If provided as input, the same variables will be returned.
                If not provided, new variables will be declared and returned.
        """
        pulse: BaseReadoutPulse = self.operations[pulse_name]

        if num_segments is None and segment_length is None:
            raise ValueError(
                "InOutSingleChannel.measure_accumulated requires either 'segment_length' "
                "or 'num_segments' to be provided."
            )
        elif num_segments is not None and segment_length is not None:
            raise ValueError(
                "InOutSingleChannel.measure_accumulated received both 'segment_length' "
                "and 'num_segments'. Please provide only one."
            )
        elif num_segments is None:
            num_segments = int(pulse.length / (4 * segment_length))  # Number of slices
        elif segment_length is None:
            segment_length = int(pulse.length / (4 * num_segments))

        if qua_vars is not None:
            if not isinstance(qua_vars, Sequence) or len(qua_vars) != 4:
                raise ValueError(
                    f"InOutSingleChannel.measure_accumulated received kwarg 'qua_vars' "
                    f"which is not a tuple of four QUA variables. Received {qua_vars=}"
                )
        else:
            qua_vars = [declare(fixed, size=num_segments) for _ in range(4)]

        if amplitude_scale is not None:
            if not isinstance(amplitude_scale, _PulseAmp):
                amplitude_scale = amp(amplitude_scale)
            pulse_name *= amplitude_scale

        integration_weight_labels = list(pulse.integration_weights_mapping)
        measure(
            pulse_name,
            self.name,
            stream,
            demod.accumulated(
                integration_weight_labels[0], qua_vars[0], segment_length, "out1"
            ),
            demod.accumulated(
                integration_weight_labels[1], qua_vars[1], segment_length, "out2"
            ),
            demod.accumulated(
                integration_weight_labels[2], qua_vars[2], segment_length, "out1"
            ),
            demod.accumulated(
                integration_weight_labels[0], qua_vars[3], segment_length, "out2"
            ),
        )
        return tuple(qua_vars)

    def measure_sliced(
        self,
        pulse_name: str,
        amplitude_scale: Union[ScalarFloat, Sequence[ScalarFloat]] = None,
        num_segments: Optional[int] = None,
        segment_length: Optional[int] = None,
        qua_vars: Optional[Tuple[QuaVariableFloat, ...]] = None,
        stream=None,
    ) -> Tuple[QuaVariableFloat, QuaVariableFloat, QuaVariableFloat, QuaVariableFloat]:
        """Perform a sliced dual demodulation measurement on this channel.

        Instead of two QUA variables (I and Q), this method returns four variables
        (II, IQ, QI, QQ)

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (Union[ScalarFloat, Sequence[ScalarFloat]]): Amplitude
                scale of the pulse. Can be either a float, qua.amp(float), or a list of
                floats.
            num_segments (int): The number of segments to accumulate.
                Should either specify this or `segment_length`.
            segment_length (int): The length of the segment to accumulate the
                measurement.
                Should either specify this or `num_segments`.
            qua_vars (Tuple[QuaVariableFloat, ...], optional): Four QUA
                variables to store the II, IQ, QI, QQ measurement results.
                If not provided, new variables will be declared and returned.
            stream (Optional[StreamType]): The stream to save the measurement result to.
                If not provided, the raw ADC signal will not be streamed.

        Returns:
            II, IQ, QI, QQ: The QUA variables used to store the measurement results.
                If provided as input, the same variables will be returned.
                If not provided, new variables will be declared and returned.
        """
        pulse: BaseReadoutPulse = self.operations[pulse_name]

        if num_segments is None and segment_length is None:
            raise ValueError(
                "InOutSingleChannel.measure_sliced requires either 'segment_length' "
                "or 'num_segments' to be provided."
            )
        elif num_segments is not None and segment_length is not None:
            raise ValueError(
                "InOutSingleChannel.measure_sliced received both 'segment_length' "
                "and 'num_segments'. Please provide only one."
            )
        elif num_segments is None:
            num_segments = int(pulse.length / (4 * segment_length))  # Number of slices
        elif segment_length is None:
            segment_length = int(pulse.length / (4 * num_segments))

        if qua_vars is not None:
            if not isinstance(qua_vars, Sequence) or len(qua_vars) != 4:
                raise ValueError(
                    f"InOutSingleChannel.measure_sliced received kwarg 'qua_vars' "
                    f"which is not a tuple of four QUA variables. Received {qua_vars=}"
                )
        else:
            qua_vars = [declare(fixed, size=num_segments) for _ in range(4)]

        if amplitude_scale is not None:
            if not isinstance(amplitude_scale, _PulseAmp):
                amplitude_scale = amp(amplitude_scale)
            pulse_name *= amplitude_scale

        integration_weight_labels = list(pulse.integration_weights_mapping)
        measure(
            pulse_name,
            self.name,
            stream,
            demod.sliced(
                integration_weight_labels[0], qua_vars[0], segment_length, "out1"
            ),
            demod.sliced(
                integration_weight_labels[1], qua_vars[1], segment_length, "out2"
            ),
            demod.sliced(
                integration_weight_labels[2], qua_vars[2], segment_length, "out1"
            ),
            demod.sliced(
                integration_weight_labels[0], qua_vars[3], segment_length, "out2"
            ),
        )
        return tuple(qua_vars)


@quam_dataclass
class InIQChannel(_InComplexChannel):
    """QUAM component for an IQ input channel

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "readout") and value is a
            ReadoutPulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_input_I (LF_input_port_types): Channel I input port from the OPX
            perspective, e.g. LFFEMAnalogInputPort("con1", 1, 1)
        opx_input_Q (LF_input_port_types): Channel Q input port from the OPX
            perspective, e.g. LFFEMAnalogInputPort("con1", 1, 2)
        opx_input_offset_I float: The offset of the I channel. Default is 0.
        opx_input_offset_Q float: The offset of the Q channel. Default is 0.
        frequency_converter_down (Optional[FrequencyConverter]): Frequency converter
            QUAM component for the IQ input port. Only needed for the old Octave.
        time_of_flight (int): Round-trip signal duration in nanoseconds.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing.
        input_gain (float): The gain of the input channel. Default is None.
    """

    opx_input_I: LF_input_port_types
    opx_input_Q: LF_input_port_types

    time_of_flight: int = 140
    smearing: int = 0

    opx_input_offset_I: float = None
    opx_input_offset_Q: float = None

    input_gain: Optional[int] = None

    frequency_converter_down: BaseFrequencyConverter = None

    _default_label: ClassVar[str] = "IQ"

    def apply_to_config(self, config: dict):
        """Adds this InOutIQChannel to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        super().apply_to_config(config)

        # Note outputs instead of inputs because it's w.r.t. the QPU
        element_config = config["elements"][self.name]
        element_config["smearing"] = self.smearing
        element_config["time_of_flight"] = self.time_of_flight

        from quam.components.octave import OctaveDownConverter

        if isinstance(self.frequency_converter_down, OctaveDownConverter):
            octave = self.frequency_converter_down.octave
            if octave is None:
                raise ValueError(
                    f"Error generating config: channel {self.name} has an "
                    f"OctaveDownConverter (id={self.frequency_converter_down.id}) "
                    "without an attached Octave"
                )
            element_config["RF_outputs"] = {
                "port": (octave.name, self.frequency_converter_down.id)
            }
        elif str_ref.is_reference(self.frequency_converter_down):
            raise ValueError(
                f"Error generating config: channel {self.name} could not determine "
                f'"frequency_converter_down", it seems to point to a non-existent '
                f"reference: {self.frequency_converter_down}"
            )
        else:
            # To be filled in next section
            element_config["outputs"] = {}

        opx_inputs = [self.opx_input_I, self.opx_input_Q]
        offsets = [self.opx_input_offset_I, self.opx_input_offset_Q]
        input_gain = int(self.input_gain if self.input_gain is not None else 0)
        for k, (opx_input, offset) in enumerate(zip(opx_inputs, offsets), start=1):
            if isinstance(opx_input, LFAnalogInputPort):
                opx_port = opx_input
            elif len(opx_input) == 2:
                opx_port = OPXPlusAnalogInputPort(
                    *opx_input, offset=offset, gain_db=input_gain
                )
                opx_port.apply_to_config(config)
            else:
                opx_port = LFFEMAnalogInputPort(
                    *opx_input, offset=offset, gain_db=input_gain
                )
                opx_port.apply_to_config(config)
            if not isinstance(self.frequency_converter_down, OctaveDownConverter):
                element_config["outputs"][f"out{k}"] = opx_port.port_tuple


@quam_dataclass
class InOutSingleChannel(SingleChannel, InSingleChannel):
    """QUAM component for a single (not IQ) input + output channel.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output (LF_output_port_types): Channel output port from the OPX
            perspective, e.g. LFFEMAnalogOutputPort("con1", 1, 2)
        opx_output_offset (float): DC offset for the output port.
        opx_input (LF_input_port_types): Channel input port from OPX perspective,
            e.g. LFFEMAnalogInputPort("con1", 1, 2)
        opx_input_offset (float): DC offset for the input port.
        filter_fir_taps (List[float]): FIR filter taps for the output port.
        filter_iir_taps (List[float]): IIR filter taps for the output port.
        intermediate_frequency (float): Intermediate frequency of OPX output, default
            is None.
        time_of_flight (int): Round-trip signal duration in nanoseconds.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing.
    """

    pass


@quam_dataclass
class InOutIQChannel(IQChannel, InIQChannel):
    """QUAM component for an IQ channel with both input and output.

    An example of such a channel is a readout resonator, where you may want to
    apply a readout tone and then measure the response.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "readout") and value is a
            ReadoutPulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output_I (LF_output_port_types): Channel I output port from the OPX
            perspective, e.g. LFFEMAnalogOutputPort("con1", 1, 1)
        opx_output_Q (LF_output_port_types): Channel Q output port from the OPX
            perspective, e.g. LFFEMAnalogOutputPort("con1", 1, 2)
        opx_output_offset_I (float): The offset of the I channel. Default is 0.
        opx_output_offset_Q (float): The offset of the Q channel. Default is 0.
        opx_input_I (LF_input_port_types): Channel I input port from the OPX
            perspective, e.g. LFFEMAnalogInputPort("con1", 1, 1)
        opx_input_Q (LF_input_port_types): Channel Q input port from the OPX
            perspective, e.g. LFFEMAnalogInputPort("con1", 1, 2)
        opx_input_offset_I (float): The offset of the I channel. Default is 0.
        opx_input_offset_Q (float): The offset of the Q channel. Default is 0.
        intermediate_frequency (float): Intermediate frequency of the mixer.
            Default is 0.0
        LO_frequency (float): Local oscillator frequency. Default is the LO frequency
            of the frequency converter up component.
        RF_frequency (float): RF frequency of the mixer. By default, the RF frequency
            is inferred by adding the LO frequency and the intermediate frequency.
        frequency_converter_up (FrequencyConverter): Frequency converter QUAM component
            for the IQ output.
        frequency_converter_down (Optional[FrequencyConverter]): Frequency converter
            QUAM component for the IQ input port. Only needed for the old Octave.
        time_of_flight (int): Round-trip signal duration in nanoseconds.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing.
    """

    pass


@quam_dataclass
class InSingleOutIQChannel(IQChannel, InSingleChannel):
    """QUAM component for an IQ output channel with a single input.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "readout") and value is a
            ReadoutPulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output_I (LF_output_port_types): Channel I output port from the OPX
            perspective, e.g. LFFEMAnalogOutputPort("con1", 1, 1)
        opx_output_Q (LF_output_port_types): Channel Q output port from the OPX
            perspective, e.g. LFFEMAnalogOutputPort("con1", 1, 2)
        opx_output_offset_I (float): The offset of the I channel. Default is 0.
        opx_output_offset_Q (float): The offset of the Q channel. Default is 0.
        opx_input (LF_input_port_types): Channel input port from OPX perspective,
            e.g. LFFEMAnalogInputPort("con1", 1, 1)
        opx_input_offset (float): DC offset for the input port.
        intermediate_frequency (float): Intermediate frequency of the mixer.
            Default is 0.0
        LO_frequency (float): Local oscillator frequency. Default is the LO frequency
            of the frequency converter up component.
        RF_frequency (float): RF frequency of the mixer. By default, the RF frequency
            is inferred by adding the LO frequency and the intermediate frequency.
        frequency_converter_up (FrequencyConverter): Frequency converter QUAM component
            for the IQ output.
        time_of_flight (int): Round-trip signal duration in nanoseconds.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing.
    """

    pass


@quam_dataclass
class InIQOutSingleChannel(SingleChannel, InIQChannel):
    """QUAM component for an IQ input channel with a single output.

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "readout") and value is a
            ReadoutPulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output (LF_output_port_types): Channel output port from the OPX
            perspective, e.g. LFFEMAnalogOutputPort("con1", 1, 1)
        opx_output_offset (float): DC offset for the output port.
        opx_input_I (LF_input_port_types): Channel I input port from the OPX
            perspective, e.g. LFFEMAnalogInputPort("con1", 1, 1)
        opx_input_Q (LF_input_port_types): Channel Q input port from the OPX
            perspective, e.g. LFFEMAnalogInputPort("con1", 1, 2)
        opx_input_offset_I (float): The offset of the I channel. Default is 0.
        opx_input_offset_Q (float): The offset of the Q channel. Default is 0.
        filter_fir_taps (List[float]): FIR filter taps for the output port.
        filter_iir_taps (List[float]): IIR filter taps for the output port.
        intermediate_frequency (float): Intermediate frequency of OPX output, default
            is None.
        time_of_flight (int): Round-trip signal duration in nanoseconds.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing.
    """

    pass


@quam_dataclass
class MWChannel(_OutComplexChannel):
    """QUAM component for a MW FEM output channel

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output (MWFEMAnalogOutputPort): Channel output port from the OPX perspective.
        intermediate_frequency (float): Intermediate frequency of OPX output, default
            is None.
        upconverter (int): The upconverter to use. Default is 1.
        time_of_flight (int): Round-trip signal duration in nanoseconds.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing.
    """

    opx_output: MWFEMAnalogOutputPort
    upconverter: int = 1

    LO_frequency: float = "#./upconverter_frequency"
    RF_frequency: float = "#./inferred_RF_frequency"

    def apply_to_config(self, config: Dict) -> None:
        super().apply_to_config(config)

        element_config = config["elements"][self.name]
        element_config["MWInput"] = {
            "port": self.opx_output.port_tuple,
            "upconverter": self.upconverter,
        }

    @property
    def upconverter_frequency(self) -> float:
        """Determine the upconverter frequency from the opx_output.

        If the upconverter frequency is not set, the upconverter frequency is inferred
        from the upconverters dictionary.

        Returns:
            The upconverter frequency.

        Raises:
            ValueError: If the upconverter frequency is not set and cannot be inferred.
        """
        if self.opx_output.upconverter_frequency is not None:
            return self.opx_output.upconverter_frequency
        if self.opx_output.upconverters is not None:
            return self.opx_output.upconverters[self.upconverter]
        raise ValueError(
            "MWChannel: Either upconverter_frequency or upconverters must be provided"
        )


@quam_dataclass
class InMWChannel(_InComplexChannel):
    """QUAM component for a MW FEM input channel

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_input (MWFEMAnalogInputPort): Channel input port from the OPX
            perspective, e.g. MWFEMAnalogInputPort("con1", 1, 1)
        intermediate_frequency (float): Intermediate frequency of OPX output, default
            is None.
        time_of_flight (int): Round-trip signal duration in nanoseconds. Default is 280,
            which is a reasonable default for the MW FEM.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing. Default is 0.
    """

    opx_input: MWFEMAnalogInputPort

    time_of_flight: int = 280
    smearing: int = 0

    def apply_to_config(self, config: Dict) -> None:
        super().apply_to_config(config)

        element_config = config["elements"][self.name]
        element_config["MWOutput"] = {"port": self.opx_input.port_tuple}
        element_config["smearing"] = self.smearing
        element_config["time_of_flight"] = self.time_of_flight


@quam_dataclass
class InOutMWChannel(MWChannel, InMWChannel):
    """QUAM component for a MW FEM input channel

    Args:
        operations (Dict[str, Pulse]): A dictionary of pulses to be played on this
            channel. The key is the pulse label (e.g. "X90") and value is a Pulse.
        id (str, int): The id of the channel, used to generate the name.
            Can be a string, or an integer in which case it will add
            `Channel._default_label`.
        opx_output (MWFEMAnalogOutputPort): Channel output port from the OPX
            perspective, e.g. MWFEMAnalogOutputPort("con1", 1, 1)
        opx_input (MWFEMAnalogInputPort): Channel input port from the OPX
            perspective, e.g. MWFEMAnalogInputPort("con1", 1, 1)
        intermediate_frequency (float): Intermediate frequency of OPX output, default
            is None.
        upconverter (int): The upconverter to use. Default is 1.
        time_of_flight (int): Round-trip signal duration in nanoseconds.
        smearing (int): Additional window of ADC integration in nanoseconds.
            Used to account for signal smearing.
    """

    pass
