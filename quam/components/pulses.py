from abc import ABC, abstractmethod
from dataclasses import dataclass
import numbers
from typing import ClassVar, List, Union, Tuple
import numpy as np

from quam.core import QuamComponent
from quam.utils import patch_dataclass
from quam.utils.string_reference import DELIMITER

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10


__all__ = ["Pulse", "DragPulse", "SquarePulse", "GaussianPulse"]


@dataclass(kw_only=True, eq=False)
class Pulse(QuamComponent, ABC):
    operation: ClassVar[str] = "control"
    length: int

    digital_marker: Union[str, List[Tuple[int, int]]] = None

    @property
    def full_name(self):
        name = self._get_parent_attr_name()
        channel = self._get_referenced_value("#../../")
        return f"{channel.name}{DELIMITER}{name}"

    @property
    def pulse_name(self):
        return f"{self.full_name}{DELIMITER}pulse"

    @property
    def waveform_name(self):
        return f"{self.full_name}{DELIMITER}wf"

    @property
    def digital_marker_name(self):
        return f"{self.full_name}{DELIMITER}dm"

    def calculate_waveform(self):
        waveform = self.waveform_function()

        # Optionally convert IQ waveforms to complex waveform
        if isinstance(waveform, tuple) and len(waveform) == 2:
            if isinstance(waveform[0], (list, np.ndarray)):
                waveform = np.array(waveform[0]) + 1.0j * np.array(waveform[1])
            else:
                waveform = waveform[0] + 1.0j * waveform[1]

        return waveform

    @abstractmethod
    def waveform_function(self) -> List[Union[float, complex]]:
        """Function that returns the waveform of the pulse.

        Can be either a list of floats, a list of complex numbers, or a tuple of two
        lists.
        This function is called from `calculate_waveform` with the kwargs of the
        dataclass instance as arguments. Each kwarg should therefore correspond to a
        dataclass field.
        """
        ...

    def _config_add_pulse(self, config):
        assert self.operation in ["control", "measurement"]
        assert isinstance(self.length, int)

        pulse_config = config["pulses"][self.pulse_name] = {
            "operation": self.operation,
            "length": self.length,
            "waveforms": {},
        }
        if self.digital_marker is not None:
            pulse_config["digital_marker"] = self.digital_marker

        return pulse_config

    def _config_add_waveforms(self, config):
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
        from quam.components import SingleChannel, IQChannel

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
                waveform_name += f"{DELIMITER}{suffix}"

            sample_label = "sample" if wf_type == "constant" else "samples"

            config["waveforms"][waveform_name] = {
                "type": wf_type,
                sample_label: waveform,
            }
            pulse_config["waveforms"][suffix] = waveform_name

    def _config_add_digital_markers(self, config):
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
        self._config_add_pulse(config)
        self._config_add_waveforms(config)

        if self.digital_marker:
            self._config_add_digital_markers(config)


@dataclass(kw_only=True, eq=False)
class ReadoutPulse(Pulse, ABC):
    operation: ClassVar[str] = "measurement"
    digital_marker: str = "ON"

    threshold: int = 0.0
    rus_exit_threshold: int = 0.0

    @property
    def iw1_name(self):
        return f"{self.full_name}{DELIMITER}iw1"

    @property
    def iw2_name(self):
        return f"{self.full_name}{DELIMITER}iw2"

    @property
    def iw3_name(self):
        return f"{self.full_name}{DELIMITER}iw3"

    @abstractmethod
    def integration_weights_function(self) -> List[Tuple[Union[complex, float], int]]:
        ...

    def _config_add_integration_weights(self, config: dict):
        iw = self.integration_weights_function()

        if not isinstance(iw, (list, np.ndarray)):
            raise ValueError("unsupported return type")

        config["integration_weights"][self.iw1_name] = {
            "cosine": [(sample.real, length) for sample, length in iw],
            "sine": [(-sample.imag, length) for sample, length in iw],
        }
        config["integration_weights"][self.iw2_name] = {
            "cosine": [(sample.imag, length) for sample, length in iw],
            "sine": [(sample.real, length) for sample, length in iw],
        }
        config["integration_weights"][self.iw3_name] = {
            "cosine": [(-sample.imag, length) for sample, length in iw],
            "sine": [(-sample.real, length) for sample, length in iw],
        }

        config["pulses"][self.pulse_name]["integration_weights"] = {
            "iw1": self.iw1_name,
            "iw2": self.iw2_name,
            "iw3": self.iw3_name,
        }

    def apply_to_config(self, config: dict) -> None:
        super().apply_to_config(config)
        self._config_add_integration_weights(config)


@dataclass(kw_only=True, eq=False)
class ConstantReadoutPulse(ReadoutPulse):
    amplitude: Union[complex, float]
    rotation_angle: float = 0.0

    def integration_weights_function(self) -> List[Tuple[Union[complex, float], int]]:
        return [(np.exp(1j * self.rotation_angle), self.length)]

    def waveform_function(self):
        # This should probably be complex because the pulse needs I and Q
        return complex(self.amplitude)


@dataclass(kw_only=True, eq=False)
class DragPulse(Pulse):
    rotation_angle: float
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

        rotation_angle_rad = np.pi * self.rotation_angle / 180
        I_rot = I * np.cos(rotation_angle_rad) - Q * np.sin(rotation_angle_rad)
        Q_rot = I * np.sin(rotation_angle_rad) + Q * np.cos(rotation_angle_rad)

        return I_rot + 1.0j * Q_rot


@dataclass(kw_only=True, eq=False)
class SquarePulse(Pulse):
    amplitude: float

    def waveform_function(self):
        return self.amplitude


@dataclass(kw_only=True, eq=False)
class GaussianPulse(Pulse):
    amplitude: float
    length: int
    sigma: float
    subtracted: bool = True

    def waveform_function(self):
        t = np.arange(self.length, dtype=int)
        center = (self.length - 1) / 2
        gauss_wave = self.amplitude * np.exp(
            -((t - center) ** 2) / (2 * self.sigma**2)
        )

        if self.subtracted:
            gauss_wave = gauss_wave - gauss_wave[-1]
        return gauss_wave
