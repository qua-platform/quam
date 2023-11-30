from abc import ABC, abstractmethod
from dataclasses import dataclass
import numbers
from typing import Any, ClassVar, Dict, List, Union, Tuple
import numpy as np

from quam.core import QuamComponent
from quam.utils import patch_dataclass
from quam.utils import string_reference as str_ref


patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10


__all__ = [
    "Pulse",
    "ReadoutPulse",
    "ConstantReadoutPulse",
    "DragPulse",
    "SquarePulse",
    "GaussianPulse",
    "FlatTopGaussianPulse",
]


@dataclass(kw_only=True, eq=False)
class Pulse(QuamComponent, ABC):
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

    digital_marker: Union[str, List[Tuple[int, int]]] = None

    @property
    def full_name(self):
        name = self.parent.get_attr_name(self)
        channel = self._get_referenced_value("#../../")
        return f"{channel.name}{str_ref.DELIMITER}{name}"

    @property
    def pulse_name(self):
        return f"{self.full_name}{str_ref.DELIMITER}pulse"

    @property
    def waveform_name(self):
        return f"{self.full_name}{str_ref.DELIMITER}wf"

    @property
    def digital_marker_name(self):
        return f"{self.full_name}{str_ref.DELIMITER}dm"

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

    @abstractmethod
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
            "waveforms": {},
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
        pulse_config = config["pulses"][self.pulse_name]

        waveform = self.calculate_waveform()
        if waveform is None:
            return

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
        else:
            raise ValueError("unsupported return type")

        # Add check that waveform type (single or IQ) matches parent
        parent_channel = getattr(getattr(self, "parent", None), "parent", None)
        from quam.components.channels import SingleChannel, IQChannel

        parent_is_channel = isinstance(parent_channel, (IQChannel, SingleChannel))
        if parent_channel is not None and parent_is_channel:
            if "single" in waveforms and isinstance(parent_channel, IQChannel):
                raise ValueError(
                    "Waveform type 'single' not allowed for IQChannel"
                    f" '{parent_channel.name}'"
                )
            elif "I" in waveforms and isinstance(parent_channel, SingleChannel):
                raise ValueError(
                    "Waveform type 'IQ' not allowed for SingleChannel"
                    f" '{parent_channel.name}'"
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
        self._config_add_pulse(config)
        self._config_add_waveforms(config)

        if self.digital_marker:
            self._config_add_digital_markers(config)


@dataclass(kw_only=True, eq=False)
class ReadoutPulse(Pulse, ABC):
    """QuAM abstract base component for a readout pulse.

    Args:
        length (int): The length of the pulse in samples.
        digital_marker (str, list, optional): The digital marker to use for the pulse.
            Default is "ON".
    """

    operation: ClassVar[str] = "measurement"
    digital_marker: str = "ON"

    # TODO Understand why the thresholds were added.
    threshold: int = 0.0
    rus_exit_threshold: int = 0.0

    @property
    def integration_weights_names(self):
        return [f"{self.full_name}{str_ref.DELIMITER}iw{k}" for k in [1, 2, 3]]

    @property
    def integration_weights_mapping(self):
        return dict(zip(["iw1", "iw2", "iw3"], self.integration_weights_names))

    @abstractmethod
    def integration_weights_function(self) -> List[Tuple[Union[complex, float], int]]:
        """Abstract method to calculate the integration weights."""
        ...

    def _config_add_integration_weights(self, config: dict):
        """Add the integration weights to the config"""
        iw = self.integration_weights_function()

        if not isinstance(iw, (list, np.ndarray)):
            raise ValueError("unsupported return type")

        config["integration_weights"][self.integration_weights_names[0]] = {
            "cosine": [(sample.real, length) for sample, length in iw],
            "sine": [(-sample.imag, length) for sample, length in iw],
        }
        config["integration_weights"][self.integration_weights_names[1]] = {
            "cosine": [(sample.imag, length) for sample, length in iw],
            "sine": [(sample.real, length) for sample, length in iw],
        }
        config["integration_weights"][self.integration_weights_names[2]] = {
            "cosine": [(-sample.imag, length) for sample, length in iw],
            "sine": [(-sample.real, length) for sample, length in iw],
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


@dataclass(kw_only=True, eq=False)
class ConstantReadoutPulse(ReadoutPulse):
    """QuAM component for a constant readout pulse.

    Args:
        length (int): The length of the pulse in samples.
        digital_marker (str, list, optional): The digital marker to use for the pulse.
            Default is "ON".
        amplitude (float): The constant amplitude of the pulse.
        rotation_axis (float, optional): IQ rotation axis of the pulse in degrees.
            If None (default), the pulse is meant for a single channel.
            If not None, the pulse is meant for an IQ channel.
        rotation_angle (float, optional): The rotation angle for the integration weights
            in degrees.
    """

    amplitude: float
    rotation_axis: float = None
    rotation_angle: float = 0.0

    def integration_weights_function(self) -> List[Tuple[Union[complex, float], int]]:
        return [(np.exp(1j * self.rotation_angle), self.length)]

    def waveform_function(self):
        # This should probably be complex because the pulse needs I and Q
        return complex(self.amplitude)


@dataclass(kw_only=True, eq=False)
class DragPulse(Pulse):
    """Gaussian-based DRAG pulse that compensate for the leakage and AC stark shift.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    Args:
        length (int): The pulse length in ns.
        axis_angle (float): The axis rotation angle for the pulse in degrees.
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

        axis_angle_rad = np.pi * self.axis_angle / 180
        I_rot = I * np.cos(axis_angle_rad) - Q * np.sin(axis_angle_rad)
        Q_rot = I * np.sin(axis_angle_rad) + Q * np.cos(axis_angle_rad)

        return I_rot + 1.0j * Q_rot


@dataclass(kw_only=True, eq=False)
class SquarePulse(Pulse):
    """Square pulse QuAM component.

    Args:
        length (int): The length of the pulse in samples.
        digital_marker (str, list, optional): The digital marker to use for the pulse.
        amplitude (float): The amplitude of the pulse in volts.
            Either a float for a single channel, or a complex number for an IQ channel.
        rotation_axis (float, optional): IQ rotation axis of the pulse in degrees.
            If None (default), the pulse is meant for a single channel.
            If not None, the pulse is meant for an IQ channel.
    """

    amplitude: float
    rotation_axis: float = None

    def waveform_function(self):
        waveform = self.amplitude

        if self.rotation_axis is not None:
            waveform = waveform * np.exp(1j * np.pi * self.rotation_axis / 180)
        return waveform


@dataclass(kw_only=True, eq=False)
class GaussianPulse(Pulse):
    """Gaussian pulse QuAM component.

    Args:
        amplitude (float): The amplitude of the pulse in volts.
        length (int): The length of the pulse in samples.
        sigma (float): The standard deviation of the gaussian pulse.
            Should generally be less than half the length of the pulse.
        rotation_axis (float, optional): IQ rotation axis of the pulse in degrees.
            If None (default), the pulse is meant for a single channel.
            If not None, the pulse is meant for an IQ channel.
        subtracted (bool): If true, returns a subtracted Gaussian, such that the first
            and last points will be at 0 volts. This reduces high-frequency components
            due to the initial and final points offset. Default is true.
    """

    amplitude: float
    length: int
    sigma: float
    rotation_axis: float = None
    subtracted: bool = True

    def waveform_function(self):
        t = np.arange(self.length, dtype=int)
        center = (self.length - 1) / 2
        waveform = self.amplitude * np.exp(-((t - center) ** 2) / (2 * self.sigma**2))

        if self.subtracted:
            waveform = waveform - waveform[-1]

        if self.rotation_axis is not None:
            waveform = waveform * np.exp(1j * np.pi * self.rotation_axis / 180)

        return waveform


@dataclass(kw_only=True, eq=False)
class FlatTopGaussianPulse(Pulse):
    """Gaussian pulse with flat top QuAM component.

    Args:
        length (int): The total length of the pulse in samples.
        amplitude (float): The amplitude of the pulse in volts.
        rotation_axis (float, optional): IQ rotation axis of the pulse in degrees.
            If None (default), the pulse is meant for a single channel.
            If not None, the pulse is meant for an IQ channel.
        flat_length (int): The length of the pulse's flat top in samples.
            The rise and fall lengths are calculated from the total length and the
            flat length.
    """

    amplitude: float
    rotation_axis: float = None
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

        if self.rotation_axis is not None:
            waveform = waveform * np.exp(1j * np.pi * self.rotation_axis / 180)

        return waveform
