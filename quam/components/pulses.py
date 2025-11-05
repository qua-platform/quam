import numbers
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from quam.core import QuamComponent, quam_dataclass
from quam.utils import string_reference as str_ref
from quam.utils.qua_types import ChirpType, ScalarBool, ScalarFloat, ScalarInt, StreamType

__all__ = [
    "Pulse",
    "BaseReadoutPulse",
    "ReadoutPulse",
    "WaveformPulse",
    "DragGaussianPulse",
    "DragCosinePulse",
    "DragPulse",
    "SquarePulse",
    "SquareReadoutPulse",
    "GaussianPulse",
    "FlatTopGaussianPulse",
    "ConstantReadoutPulse",
    "FlatTopBlackmanPulse",
    "BlackmanIntegralPulse",
    "FlatTopTanhPulse",
    "FlatTopCosinePulse",
    "CosineBipolarPulse",
]


@quam_dataclass
class Pulse(QuamComponent):
    """QUAM base component for a pulse.

    Pulses are added to a channel using
    ```
    channel.operations["pulse_name"] = pulse
    ```

    The `Pulse` class is an abstract base class, and should not be instantiated
    directly. Instead, use one of the subclasses such as:
    - `ConstantReadoutPulse`
    - `DragPulse`
    - `SquarePulse`
    - `GaussianPulse`
    or create a custom subclass. In this case, the method `waveform_function` should
    be implemented.

    Args:
        operation (str): The operation of the pulse, either "control" or "measurement".
            Default is "control".
        length (int): The length of the pulse in samples.
        digital_marker (str, list, optional): The digital marker to use for the pulse.
            Can be a string, in which case it is a reference to a digital marker in the
            config, or a list of tuples of (sample, length) pairs. Default is None.

    Note:
        The unique pulse label is automatically generated from the channel name and
        the pulse name, the same for the waveform and digital marker names.
        The pulse label is defined as `"{channel_name}.{pulse_name}.pulse"`.
        The waveform label is defined as `"{channel_name}.{pulse_name}.wf"`.
        The digital marker label is defined as `"{channel_name}.{pulse_name}.dm"`.

    """

    operation: ClassVar[str] = "control"
    length: int
    id: str = None

    digital_marker: Union[str, List[Tuple[int, int]]] = None

    @property
    def channel(self):
        """The channel to which the pulse is attached, None if no channel is attached"""
        from quam.components.channels import Channel

        if isinstance(self.parent, Channel):
            return self.parent
        elif hasattr(self.parent, "parent") and isinstance(self.parent.parent, Channel):
            return self.parent.parent
        else:
            return None

    @property
    def name(self):
        if self.channel is None:
            raise AttributeError(f"Cannot get full name of pulse '{self}' because it is not" " attached to a channel")

        if self.id is not None:
            name = self.id
        else:
            name = self.parent.get_attr_name(self)

        return f"{self.channel.name}{str_ref.DELIMITER}{name}"

    @property
    def pulse_name(self):
        return f"{self.name}{str_ref.DELIMITER}pulse"

    @property
    def waveform_name(self):
        return f"{self.name}{str_ref.DELIMITER}wf"

    @property
    def digital_marker_name(self):
        return f"{self.name}{str_ref.DELIMITER}dm"

    def calculate_waveform(
        self,
    ) -> Union[float, complex, Sequence[float], Sequence[complex]]:
        """Calculate the waveform of the pulse.

        This function calls `Pulse.waveform_function`, which should generally be
        subclassed, to generate the waveform.

        This function then processes the results such that IQ waveforms are cast
        into complex values.

        Returns:
            The processed waveform, which can be either
            - a single float for a constant single-channel waveform,
            - a single complex number for a constant IQ waveform,
            - a sequence of floats for an arbitrary single-channel waveform,
            - a sequence of complex numbers for an arbitrary IQ waveform,
        """
        waveform = self.waveform_function()

        # Optionally convert IQ waveforms to complex waveform
        if isinstance(waveform, tuple) and len(waveform) == 2:
            if isinstance(waveform[0], (list, np.ndarray)):
                waveform = np.array(waveform[0]) + 1.0j * np.array(waveform[1])
            else:
                waveform = waveform[0] + 1.0j * waveform[1]

        return waveform

    def waveform_function(
        self,
    ) -> Union[
        float,
        complex,
        Sequence[float],
        Sequence[complex],
        Tuple[float, float],
        Tuple[Sequence[float], Sequence[float]],
    ]:
        """Function that returns the waveform of the pulse.

        The waveform function should use the relevant parameters from the pulse, which
        is passed as the only argument.

        This function is called from `Pulse.calculate_waveform`

        Returns:
            The waveform of the pulse. Can be one of the following:
            - a single float for a constant single-channel waveform,
            - a single complex number for a constant IQ waveform,
            - a sequence of floats for an arbitrary single-channel waveform,
            - a sequence of complex numbers for an arbitrary IQ waveform,
            - a tuple of floats for a constant IQ waveform,
            - a tuple of sequences for an arbitrary IQ waveform
        """
        ...

    def play(
        self,
        amplitude_scale: Optional[Union[ScalarFloat, Sequence[ScalarFloat]]] = None,
        duration: ScalarInt = None,
        condition: ScalarBool = None,
        chirp: ChirpType = None,
        truncate: ScalarInt = None,
        timestamp_stream: StreamType = None,
        continue_chirp: bool = False,
        target: str = "",
        validate: bool = True,
    ) -> None:
        """Play the pulse on the channel.

        The corresponding channel to play the pulse on is determined from the
        parent of the pulse.

        Args:
            pulse_name (str): The name of the pulse to play. Should be registered in
                `self.operations`.
            amplitude_scale (Optional[Union[ScalarFloat, Sequence[ScalarFloat]]]):
                Amplitude scale of the pulse. Can be either a (qua) float, or a list of
                (qua) floats. If None, the pulse is played without amplitude scaling.
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
            truncate (Scalar[int]): Allows playing
                only part of the pulse, truncating the end. If provided,
                will play only up to the given time in units of the clock
                cycle (4ns).
            condition (Scalar[bool]): Will play analog
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

        Raises:
            ValueError: If the pulse is not attached to a channel.
            KeyError: If the pulse is not registered in the channel's operations.
        """
        if self.id is not None:
            name = self.id
        elif self.parent is not None:
            name = self.parent.get_attr_name(self)
        else:
            raise ValueError(f"Cannot determine name of pulse '{self}'")

        if self.channel is None:
            raise ValueError(f"Pulse '{name}' is not attached to a channel")

        self.channel.play(
            pulse_name=name,
            amplitude_scale=amplitude_scale,
            duration=duration,
            condition=condition,
            chirp=chirp,
            truncate=truncate,
            timestamp_stream=timestamp_stream,
            continue_chirp=continue_chirp,
            target=target,
            validate=validate,
        )

    def _config_add_pulse(self, config: Dict[str, Any]):
        """Add the pulse to the config

        The config entry is added to `config["pulses"][self.pulse_name]`
        """
        assert self.operation in ["control", "measurement"]
        assert isinstance(self.length, int)

        pulse_config = config["pulses"][self.pulse_name] = {
            "operation": self.operation,
            "length": self.length,
        }

    def _config_add_waveforms(self, config):
        """Add the waveform to the config

        For a single waveform, the config entry is added to
        `config["waveforms"]["{channel_name}.{pulse_name}.wf"]`.
        For an IQ waveform, two config entries are added to
        `config["waveforms"]["{channel_name}.{pulse_name}.wf.I"]` and with suffix `Q`.

        Raises:
            ValueError: If the waveform type (single or IQ) does not match the parent
                channel type (SingleChannel, IQChannel, InOutIQChannel, MWChannel,
                InOutMWChannel).
        """

        from quam.components.channels import IQChannel, MWChannel, SingleChannel

        pulse_config = config["pulses"][self.pulse_name]

        waveform = self.calculate_waveform()
        if waveform is None:
            return

        pulse_config["waveforms"] = {}

        if isinstance(waveform, numbers.Number):
            wf_type = "constant"
            if isinstance(waveform, complex):
                waveforms = {"I": waveform.real, "Q": waveform.imag}
            elif isinstance(self.channel, (IQChannel, MWChannel)):
                waveforms = {"I": waveform, "Q": 0.0}
            else:
                waveforms = {"single": waveform}

        elif isinstance(waveform, (list, np.ndarray)):
            wf_type = "arbitrary"
            if np.iscomplexobj(waveform):
                waveforms = {"I": list(waveform.real), "Q": list(waveform.imag)}
            elif isinstance(self.channel, (IQChannel, MWChannel)):
                waveforms = {"I": list(waveform), "Q": list(np.zeros_like(waveform))}
            else:
                waveforms = {"single": list(waveform)}
        else:
            raise ValueError("unsupported return type")

        # Add check that waveform type (single or IQ) matches parent
        if "single" in waveforms and not isinstance(self.channel, SingleChannel):
            raise ValueError("Waveform type 'single' not allowed for (IQChannel, MWChannel)" f" '{self.channel.name}'")
        elif "I" in waveforms and not isinstance(self.channel, (IQChannel, MWChannel)):
            raise ValueError("Waveform type 'IQ' not allowed for SingleChannel" f" '{self.channel.name}'")

        for suffix, waveform in waveforms.items():
            waveform_name = self.waveform_name
            if suffix != "single":
                waveform_name += f"{str_ref.DELIMITER}{suffix}"

            sample_label = "sample" if wf_type == "constant" else "samples"

            config["waveforms"][waveform_name] = {
                "type": wf_type,
                sample_label: waveform,
            }
            pulse_config["waveforms"][suffix] = waveform_name

    def _config_add_digital_markers(self, config):
        """Add the digital marker to the config

        The config entry is added to
        `config["digital_waveforms"]["{channel_name}.{pulse_name}.dm"]` and also
        registered in
        `config["pulses"]["{channel_name}.{pulse_name}.pulse"]["digital_marker"]`.

        If the digital marker is a string, it is assumed to be a reference to a
        digital marker already defined in the config.
        """
        if isinstance(self.digital_marker, str):
            # Use a common config digital marker
            if self.digital_marker not in config["digital_waveforms"]:
                raise KeyError("{self.name}.digital_marker={self.digital_marker} not in" " config['digital_waveforms']")
            digital_marker_name = self.digital_marker
        else:
            digital_marker_list = [tuple(t) for t in self.digital_marker]
            config["digital_waveforms"][self.digital_marker_name] = {"samples": digital_marker_list}
            digital_marker_name = self.digital_marker_name

        config["pulses"][self.pulse_name]["digital_marker"] = digital_marker_name

    def apply_to_config(self, config: dict) -> None:
        """Adds this pulse, waveform, and digital marker to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        if self.channel is None:
            return

        self._config_add_pulse(config)
        self._config_add_waveforms(config)

        if self.digital_marker:
            self._config_add_digital_markers(config)


@quam_dataclass
class BaseReadoutPulse(Pulse, ABC):
    """QUAM abstract base component for a general  readout pulse.

    Readout pulse classes should usually inherit from `ReadoutPulse`, the
    exception being when a custom integration weights function is required.

    Args:
        length (int): The length of the pulse in samples.
        digital_marker (str, list, optional): The digital marker to use for the pulse.
            Default is "ON".
    """

    operation: ClassVar[str] = "measurement"
    digital_marker: str = "ON"

    # TODO Understand why the thresholds were added.
    threshold: float = None
    rus_exit_threshold: float = None

    _weight_labels: ClassVar[List[str]] = ["iw1", "iw2", "iw3"]

    @property
    def integration_weights_names(self):
        return [f"{self.name}{str_ref.DELIMITER}{name}" for name in self._weight_labels]

    @property
    def integration_weights_mapping(self):
        return dict(zip(self._weight_labels, self.integration_weights_names))

    @abstractmethod
    def integration_weights_function(self) -> Dict[str, List[Tuple[float, int]]]:
        """Abstract method to calculate the integration weights.

        Returns:
            Dict containing keys "real", "imag", "minus_real", "minus_imag".
            Values are lists of tuples of (weight, length) pairs.
        """
        ...

    def _config_add_integration_weights(self, config: dict):
        """Add the integration weights to the config"""
        integration_weights = self.integration_weights_function()

        config["integration_weights"][self.integration_weights_names[0]] = {
            "cosine": integration_weights["real"],
            "sine": integration_weights["minus_imag"],
        }
        config["integration_weights"][self.integration_weights_names[1]] = {
            "cosine": integration_weights["imag"],
            "sine": integration_weights["real"],
        }
        config["integration_weights"][self.integration_weights_names[2]] = {
            "cosine": integration_weights["minus_imag"],
            "sine": integration_weights["minus_real"],
        }

        pulse_config = config["pulses"][self.pulse_name]
        pulse_config["integration_weights"] = self.integration_weights_mapping

    def apply_to_config(self, config: dict) -> None:
        """Adds this readout pulse to the QUA configuration.

        See [`QuamComponent.apply_to_config`][quam.core.quam_classes.QuamComponent.apply_to_config]
        for details.
        """
        super().apply_to_config(config)
        self._config_add_integration_weights(config)


@quam_dataclass
class ReadoutPulse(BaseReadoutPulse, ABC):
    """QUAM abstract base component for most readout pulses.

    This class is a subclass of `ReadoutPulse` and should be used for most readout
    pulses. It provides a default implementation of the `integration_weights_function`
    method, which is suitable for most cases.

    Args:
        length (int): The length of the pulse in samples.
        digital_marker (str, list, optional): The digital marker to use for the pulse.
            Default is "ON".
        integration_weights (list[float], list[tuple[float, int]], optional): The
            integration weights, can be either
            - a list of floats (one per sample), the length must match the pulse length
            - a list of tuples of (weight, length) pairs, the sum of the lengths must
              match the pulse length
        integration_weights_angle (float, optional): The rotation angle for the
            integration weights in radians.
    """

    integration_weights: Union[List[float], List[Tuple[float, int]]] = "#./default_integration_weights"
    integration_weights_angle: float = 0

    @property
    def default_integration_weights(self) -> List[Tuple[float, int]]:
        return [(1, self.length)]

    def integration_weights_function(self) -> List[Tuple[Union[complex, float], int]]:
        from qualang_tools.config import convert_integration_weights

        phase = np.exp(1j * self.integration_weights_angle)

        if isinstance(self.integration_weights[0], float):
            integration_weights = convert_integration_weights(self.integration_weights)
        else:
            integration_weights = self.integration_weights

        return {
            "real": [(phase.real * w, l) for w, l in integration_weights],
            "imag": [(phase.imag * w, l) for w, l in integration_weights],
            "minus_real": [(-phase.real * w, l) for w, l in integration_weights],
            "minus_imag": [(-phase.imag * w, l) for w, l in integration_weights],
        }


@quam_dataclass
class WaveformPulse(Pulse):
    """Pulse that uses a pre-defined waveform, as opposed to a function.

    For a single channel, only `waveform_I` is required.
    For an IQ channel, both `waveform_I` and `waveform_Q` are required.

    The length of the pulse is derived from the length of `waveform_I`.

    Args:
        waveform_I (list[float]): The in-phase waveform.
        waveform_Q (list[float], optional): The quadrature waveform.
    """

    waveform_I: List[float]  # pyright: ignore
    waveform_Q: Optional[List[float]] = None
    # Length is derived from the waveform_I length, but still needs to be declared
    # to satisfy the dataclass, but we'll override its behavior
    length: Optional[int] = None  # pyright: ignore

    @property
    def length(self):  # noqa: 811
        if not isinstance(self.waveform_I, Iterable):
            return None
        return len(self.waveform_I)

    @length.setter
    def length(self, length: Optional[int]):
        if length is not None and not isinstance(length, property):
            raise AttributeError(f"length is not writable with value {length}")

    def waveform_function(self):
        if self.waveform_Q is None:
            return np.array(self.waveform_I)
        return np.array(self.waveform_I) + 1.0j * np.array(self.waveform_Q)

    def to_dict(self, follow_references: bool = False, include_defaults: bool = False) -> Dict[str, Any]:
        d = super().to_dict(follow_references, include_defaults)
        d.pop("length")
        return d


@quam_dataclass
class DragGaussianPulse(Pulse):
    """Gaussian-based DRAG pulse that compensate for the leakage and AC stark shift.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    Args:
        length (int): The pulse length in ns.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is meant for a single channel or the I port
                of an IQ channel
            If not None, the pulse is meant for an IQ channel (0 is X, pi/2 is Y).
        amplitude (float): The amplitude in volts.
        sigma (float): The gaussian standard deviation.
        alpha (float): The DRAG coefficient.
        anharmonicity (float): f_21 - f_10 - The differences in energy between the 2-1
            and the 1-0 energy levels, in Hz.
        detuning (float): The frequency shift to correct for AC stark shift, in Hz.
        subtracted (bool): If true, returns a subtracted Gaussian, such that the first
            and last points will be at 0 volts. This reduces high-frequency components
            due to the initial and final points offset. Default is true.

    """

    axis_angle: float
    amplitude: float
    sigma: float
    alpha: float
    anharmonicity: float
    detuning: float = 0.0
    subtracted: bool = True

    def __post_init__(self) -> None:
        return super().__post_init__()

    def waveform_function(self):
        from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

        I, Q = drag_gaussian_pulse_waveforms(
            amplitude=self.amplitude,
            length=self.length,
            sigma=self.sigma,
            alpha=self.alpha,
            anharmonicity=self.anharmonicity,
            detuning=self.detuning,
            subtracted=self.subtracted,
        )
        I, Q = np.array(I), np.array(Q)

        I_rot = I * np.cos(self.axis_angle) - Q * np.sin(self.axis_angle)
        Q_rot = I * np.sin(self.axis_angle) + Q * np.cos(self.axis_angle)

        return I_rot + 1.0j * Q_rot


@quam_dataclass
class DragPulse(DragGaussianPulse):
    def __post_init__(self) -> None:
        warnings.warn(
            "DragPulse is deprecated. Use DragGaussianPulse instead.",
            DeprecationWarning,
        )
        return super().__post_init__()


@quam_dataclass
class DragCosinePulse(Pulse):
    """Cosine based DRAG pulse that compensate for the leakage and AC stark shift.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    Args:
        length (int): The pulse length in ns.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is meant for a single channel or the I port
                of an IQ channel
            If not None, the pulse is meant for an IQ channel (0 is X, pi/2 is Y).
        amplitude (float): The amplitude in volts.
        alpha (float): The DRAG coefficient.
        anharmonicity (float): f_21 - f_10 - The differences in energy between the 2-1
            and the 1-0 energy levels, in Hz.
        detuning (float): The frequency shift to correct for AC stark shift, in Hz.
    """

    axis_angle: float
    amplitude: float
    alpha: float
    anharmonicity: float
    detuning: float = 0.0

    def __post_init__(self) -> None:
        return super().__post_init__()

    def waveform_function(self):
        from qualang_tools.config.waveform_tools import drag_cosine_pulse_waveforms

        I, Q = drag_cosine_pulse_waveforms(
            amplitude=self.amplitude,
            length=self.length,
            alpha=self.alpha,
            anharmonicity=self.anharmonicity,
            detuning=self.detuning,
        )
        I, Q = np.array(I), np.array(Q)

        I_rot = I * np.cos(self.axis_angle) - Q * np.sin(self.axis_angle)
        Q_rot = I * np.sin(self.axis_angle) + Q * np.cos(self.axis_angle)

        return I_rot + 1.0j * Q_rot


@quam_dataclass
class SquarePulse(Pulse):
    """Square pulse QUAM component.

    Args:
        length (int): The length of the pulse in samples.
        digital_marker (str, list, optional): The digital marker to use for the pulse.
        amplitude (float): The amplitude of the pulse in volts.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is meant for a single channel or the I port
                of an IQ channel
            If not None, the pulse is meant for an IQ channel (0 is X, pi/2 is Y).
    """

    amplitude: float
    axis_angle: float = None

    def waveform_function(self):
        waveform = self.amplitude

        if self.axis_angle is not None:
            waveform = waveform * np.exp(1j * self.axis_angle)
        return waveform


@quam_dataclass
class SquareReadoutPulse(ReadoutPulse, SquarePulse):
    """QUAM component for a square readout pulse.

    Args:
        length (int): The length of the pulse in samples.
        digital_marker (str, list, optional): The digital marker to use for the pulse.
            Default is "ON".
        amplitude (float): The constant amplitude of the pulse.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is meant for a single channel or the I port
                of an IQ channel
            If not None, the pulse is meant for an IQ channel (0 is X, pi/2 is Y).
        integration_weights (list[float], list[tuple[float, int]], optional): The
            integration weights, can be either
            - a list of floats (one per sample), the length must match the pulse length
            - a list of tuples of (weight, length) pairs, the sum of the lengths must
              match the pulse length
        integration_weights_angle (float, optional): The rotation angle for the
            integration weights in radians.
    """

    ...


@quam_dataclass
class ConstantReadoutPulse(SquareReadoutPulse):
    def __post_init__(self) -> None:
        warnings.warn(
            "ConstantReadoutPulse is deprecated. Use SquareReadoutPulse instead.",
            DeprecationWarning,
        )
        return super().__post_init__()


@quam_dataclass
class GaussianPulse(Pulse):
    """Gaussian pulse QUAM component.

    Args:
        amplitude (float): The amplitude of the pulse in volts.
        length (int): The length of the pulse in samples.
        sigma (float): The standard deviation of the gaussian pulse.
            Should generally be less than half the length of the pulse.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is meant for a single channel or the I port
                of an IQ channel
            If not None, the pulse is meant for an IQ channel (0 is X, pi/2 is Y).
        subtracted (bool): If true, returns a subtracted Gaussian, such that the first
            and last points will be at 0 volts. This reduces high-frequency components
            due to the initial and final points offset. Default is true.
    """

    amplitude: float
    length: int
    sigma: float
    axis_angle: float = None
    subtracted: bool = True

    def waveform_function(self):
        t = np.arange(self.length, dtype=int)
        center = (self.length - 1) / 2
        waveform = self.amplitude * np.exp(-((t - center) ** 2) / (2 * self.sigma**2))

        if self.subtracted:
            waveform = waveform - waveform[-1]

        if self.axis_angle is not None:
            waveform = waveform * np.exp(1j * self.axis_angle)

        return waveform


@quam_dataclass
class FlatTopGaussianPulse(Pulse):
    """Gaussian pulse with flat top QUAM component.

    Args:
        length (int): The total length of the pulse in samples.
        amplitude (float): The amplitude of the pulse in volts.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is meant for a single channel or the I port
                of an IQ channel
            If not None, the pulse is meant for an IQ channel (0 is X, pi/2 is Y).
        flat_length (int): The length of the pulse's flat top in samples.
            The rise and fall lengths are calculated from the total length and the
            flat length.
    """

    amplitude: float
    axis_angle: float = None
    flat_length: int

    def waveform_function(self):
        from qualang_tools.config.waveform_tools import flattop_gaussian_waveform

        rise_fall_length = (self.length - self.flat_length) // 2
        if not self.flat_length + 2 * rise_fall_length == self.length:
            raise ValueError(
                "FlatTopGaussianPulse rise_fall_length (=length-flat_length) must be"
                f" a multiple of 2 ({self.length} - {self.flat_length} ="
                f" {self.length - self.flat_length})"
            )

        waveform = flattop_gaussian_waveform(
            amplitude=self.amplitude,
            flat_length=self.flat_length,
            rise_fall_length=rise_fall_length,
            return_part="all",
        )
        waveform = np.array(waveform)

        if self.axis_angle is not None:
            waveform = waveform * np.exp(1j * self.axis_angle)

        return waveform


@quam_dataclass
class FlatTopBlackmanPulse(Pulse):
    """Blackman rise/fall, flat-top pulse.

    Args:
        length (int): Total pulse length (samples).
        amplitude (float): Peak amplitude (V).
        flat_length (int): Flat-top length (samples).
        axis_angle (float, optional): IQ axis angle in radians.
    """

    amplitude: float
    axis_angle: float = None
    flat_length: int

    def waveform_function(self):
        from qualang_tools.config.waveform_tools import flattop_blackman_waveform

        rise_fall_length = (self.length - self.flat_length) // 2
        if self.flat_length + 2 * rise_fall_length != self.length:
            raise ValueError(
                "FlatTopBlackmanPulse requires (length - flat_length) to be even "
                f"({self.length=} {self.flat_length=})"
            )

        wf = flattop_blackman_waveform(
            amplitude=self.amplitude,
            flat_length=self.flat_length,
            rise_fall_length=rise_fall_length,
            return_part="all",
        )
        wf = np.array(wf)
        if self.axis_angle is not None:
            wf = wf * np.exp(1j * self.axis_angle)
        return wf


@quam_dataclass
class BlackmanIntegralPulse(Pulse):
    """Adiabatic Blackman-integral ramp from v_start to v_end.

    Args:
        length (int): Pulse length (samples).
        v_start (float): Starting amplitude (V).
        v_end (float): Ending amplitude (V).
        axis_angle (float, optional): IQ axis angle in radians.
    """

    # amplitude: float
    v_start: float
    v_end: float
    axis_angle: float = None

    def waveform_function(self):
        from qualang_tools.config.waveform_tools import blackman_integral_waveform

        wf = blackman_integral_waveform(
            pulse_length=self.length,
            v_start=self.v_start,
            v_end=self.v_end,
        )
        wf = np.array(wf)
        if self.axis_angle is not None:
            wf = wf * np.exp(1j * self.axis_angle)
        return wf


@quam_dataclass
class FlatTopCosinePulse(Pulse):
    """Cosine rise/fall, flat-top pulse.

    Args:
        length (int): Total pulse length (samples).
        amplitude (float): Peak amplitude (V).
        flat_length (int): Flat-top length (samples).
        axis_angle (float, optional): IQ axis angle in radians.
    """

    amplitude: float
    axis_angle: float = None
    flat_length: int = 0

    def waveform_function(self):
        from qualang_tools.config.waveform_tools import flattop_cosine_waveform

        rise_fall_length = (self.length - self.flat_length) // 2
        if self.flat_length + 2 * rise_fall_length != self.length:
            raise ValueError(
                "FlatTopCosinePulse requires (length - flat_length) to be even " f"({self.length=} {self.flat_length=})"
            )

        wf = flattop_cosine_waveform(
            amplitude=self.amplitude,
            flat_length=self.flat_length,
            rise_fall_length=rise_fall_length,
            return_part="all",
        )
        wf = np.array(wf)
        if self.axis_angle is not None:
            wf = wf * np.exp(1j * self.axis_angle)
        return wf


@quam_dataclass
class FlatTopTanhPulse(Pulse):
    """tanh rise/fall, flat-top pulse.

    Args:
        length (int): Total pulse length (samples).
        amplitude (float): Peak amplitude (V).
        flat_length (int): Flat-top length (samples).
        axis_angle (float, optional): IQ axis angle in radians.
    """

    amplitude: float
    axis_angle: float = None
    flat_length: int = 0

    def waveform_function(self):
        from qualang_tools.config.waveform_tools import flattop_tanh_waveform

        rise_fall_length = (self.length - self.flat_length) // 2
        if self.flat_length + 2 * rise_fall_length != self.length:
            raise ValueError(
                "FlatTopTanhPulse requires (length - flat_length) to be even " f"({self.length=} {self.flat_length=})"
            )

        wf = flattop_tanh_waveform(
            amplitude=self.amplitude,
            flat_length=self.flat_length,
            rise_fall_length=rise_fall_length,
            return_part="all",
        )
        wf = np.array(wf)
        if self.axis_angle is not None:
            wf = wf * np.exp(1j * self.axis_angle)
        return wf


@quam_dataclass
class CosineBipolarPulse(Pulse):
    """
    CosineBipolarPulse QUAM component.

    This pulse generates a net-zero waveform composed of two symmetric cosine-shaped lobes,
    designed to minimize DC offset and long-timescale distortions. The waveform starts with a
    smooth cosine rise, transitions through a positive flat section, passes through a
    cosine-shaped switch to a negative flat section, and ends with a symmetric cosine rise.
    The positive and negative flat regions are of equal length, ensuring the total area under
    the curve is zero.

    This net-zero property makes the CosineBipolarPulse especially robust against slow baseline
    drifts and long-memory effects in experimental setups. The smooth transitions between segments reduce spectral leakage and
    high-frequency components, making this pulse suitable for sensitive quantum control
    applications.

    Increasing the total pulse length while keeping the flat length constant results in longer,
    smoother rise/fall and switch regions, further reducing spectral content at high frequencies.

    Args:
        length (int): Total length of the pulse in samples.
        amplitude (float): Peak amplitude of the pulse in volts.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is for a single channel or the I port of an IQ channel.
            If not None, the pulse is for an IQ channel (0 is X, pi/2 is Y).
        flat_length (int): Length of the flat-top region in samples (must be even and
            less than or equal to total length). The flat region is split equally between
            positive and negative halves.
    """

    amplitude: float
    axis_angle: float = None
    flat_length: int

    def waveform_function(self):
        # Helper segment generators (length 0 returns empty array)
        def halfcos(n: int):
            if n <= 0:
                return np.array([])
            t = np.arange(n) / n
            return 0.5 * (1 - np.cos(np.pi * t))

        def cos_switch(n: int):
            """
            Endpoint-exclusive cosine from +1 to -1 with zero discrete sum.
            Uses midpoint sampling: theta_k = (k + 0.5)*pi/n, k=0..n-1.
            """
            if n <= 0:
                return np.array([])
            k = np.arange(n, dtype=float)
            theta = (k + 0.5) * np.pi / n
            return np.cos(theta)  # strictly between +1 and -1, antisymmetric -> net zero

        L = int(self.length)
        F = int(self.flat_length)

        if F > L:
            raise ValueError(f"CosineBipolarPulse.flat_length ({F}) cannot exceed total length ({L}).")
        if F % 2 != 0:
            raise ValueError(
                f"CosineBipolarPulse.flat_length ({F}) must be an even number to split equally into + and - halves."
            )

        remaining = L - F
        if remaining == 0:
            rise_len = switch_len = fall_len = 0
        else:
            base = remaining // 3
            extra = remaining % 3
            rise_len = base + (1 if extra == 2 else 0)
            switch_len = base + (extra if extra == 1 else 0)
            fall_len = base + (1 if extra == 2 else 0)

        flat_pos_len = F // 2
        flat_neg_len = F // 2

        A = float(self.amplitude)

        seg_rise = A * halfcos(rise_len)
        seg_flat_pos = A * np.ones(flat_pos_len)
        seg_switch = A * cos_switch(switch_len)
        seg_flat_neg = -A * np.ones(flat_neg_len)
        seg_fall = -A * halfcos(fall_len)[::-1]

        p = np.concatenate([seg_rise, seg_flat_pos, seg_switch, seg_flat_neg, seg_fall])

        if self.axis_angle is not None:
            p = p * np.exp(1j * self.axis_angle)

        return p.tolist()
