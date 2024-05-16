from abc import ABC, abstractmethod
import numbers
import warnings
from typing import Any, ClassVar, Dict, List, Union, Tuple
import numpy as np

from quam.core import QuamComponent, quam_dataclass
from quam.utils import string_reference as str_ref


__all__ = [
    "Pulse",
    "BaseReadoutPulse",
    "ReadoutPulse",
    "DragPulse",
    "SquarePulse",
    "SquareReadoutPulse",
    "GaussianPulse",
    "FlatTopGaussianPulse",
    "ConstantReadoutPulse",
]


@quam_dataclass
class Pulse(QuamComponent):
    """QuAM base component for a pulse.

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
            raise AttributeError(
                f"Cannot get full name of pulse '{self}' because it is not"
                " attached to a channel"
            )

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

    def calculate_waveform(self) -> Union[float, complex, List[float], List[complex]]:
        """Calculate the waveform of the pulse.

        This function calls `Pulse.waveform_function`, which should generally be
        subclassed, to generate the waveform.

        This function then processes the results such that IQ waveforms are cast
        into complex values.

        Returns:
            The processed waveform, which can be either
            - a single float for a constant single-channel waveform,
            - a single complex number for a constant IQ waveform,
            - a list of floats for an arbitrary single-channel waveform,
            - a list of complex numbers for an arbitrary IQ waveform,
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
        List[float],
        List[complex],
        Tuple[float, float],
        Tuple[List[float], List[float]],
    ]:
        """Function that returns the waveform of the pulse.

        The waveform function should use the relevant parameters from the pulse, which
        is passed as the only argument.

        This function is called from `Pulse.calculate_waveform`

        Returns:
            The waveform of the pulse. Can be one of the following:
            - a single float for a constant single-channel waveform,
            - a single complex number for a constant IQ waveform,
            - a list of floats for an arbitrary single-channel waveform,
            - a list of complex numbers for an arbitrary IQ waveform,
            - a tuple of floats or float lists for an arbitrary IQ waveform
        """
        ...

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
        if self.digital_marker is not None:
            pulse_config["digital_marker"] = self.digital_marker

    def _config_add_waveforms(self, config):
        """Add the waveform to the config

        For a single waveform, the config entry is added to
        `config["waveforms"]["{channel_name}.{pulse_name}.wf"]`.
        For an IQ waveform, two config entries are added to
        `config["waveforms"]["{channel_name}.{pulse_name}.wf.I"]` and with suffix `Q`.

        Raises:
            ValueError: If the waveform type (single or IQ) does not match the parent
                channel type (SingleChannel, IQChannel, InOutIQChannel).
        """

        from quam.components.channels import SingleChannel, IQChannel

        pulse_config = config["pulses"][self.pulse_name]

        waveform = self.calculate_waveform()
        if waveform is None:
            return

        pulse_config["waveforms"] = {}

        if isinstance(waveform, numbers.Number):
            wf_type = "constant"
            if isinstance(waveform, complex):
                waveforms = {"I": waveform.real, "Q": waveform.imag}
            elif isinstance(self.channel, IQChannel):
                waveforms = {"I": waveform, "Q": 0.0}
            else:
                waveforms = {"single": waveform}

        elif isinstance(waveform, (list, np.ndarray)):
            wf_type = "arbitrary"
            if np.iscomplexobj(waveform):
                waveforms = {"I": list(waveform.real), "Q": list(waveform.imag)}
            elif isinstance(self.channel, IQChannel):
                waveforms = {"I": waveform, "Q": np.zeros_like(waveform)}
            else:
                waveforms = {"single": list(waveform)}
        else:
            raise ValueError("unsupported return type")

        # Add check that waveform type (single or IQ) matches parent
        if "single" in waveforms and not isinstance(self.channel, SingleChannel):
            raise ValueError(
                "Waveform type 'single' not allowed for IQChannel"
                f" '{self.channel.name}'"
            )
        elif "I" in waveforms and not isinstance(self.channel, IQChannel):
            raise ValueError(
                "Waveform type 'IQ' not allowed for SingleChannel"
                f" '{self.channel.name}'"
            )

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
                raise KeyError(
                    "{self.name}.digital_marker={self.digital_marker} not in"
                    " config['digital_waveforms']"
                )
            digital_marker_name = self.digital_marker
        else:
            config["digital_waveforms"][self.digital_marker_name] = {
                "samples": self.digital_marker
            }
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
    """QuAM abstract base component for a general  readout pulse.

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
    """QuAM abstract base component for most readout pulses.

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

    integration_weights: Union[List[float], List[Tuple[float, int]]] = None
    integration_weights_angle: float = 0

    def integration_weights_function(self) -> List[Tuple[Union[complex, float], int]]:
        from qualang_tools.config import convert_integration_weights

        phase = np.exp(1j * self.integration_weights_angle)

        if self.integration_weights is None or not len(self.integration_weights):
            integration_weights = [(1, self.length)]
        elif isinstance(self.integration_weights[0], float):
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
class DragPulse(Pulse):
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
class SquarePulse(Pulse):
    """Square pulse QuAM component.

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
    """QuAM component for a square readout pulse.

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
    """Gaussian pulse QuAM component.

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
    """Gaussian pulse with flat top QuAM component.

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
