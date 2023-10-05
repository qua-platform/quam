from dataclasses import dataclass
import numbers
from typing import Callable, ClassVar, Dict, List, Union, Tuple
import inspect
import numpy as np

from quam.core import QuamComponent, patch_dataclass

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10


__all__ = ["Pulse", "ReadoutPulse", "DragPulse", "SquarePulse", "GaussianPulse"]


@dataclass(kw_only=True, eq=False)
class Pulse(QuamComponent):
    operation: ClassVar[str] = "control"
    length: int

    digital_marker: Union[str, List[Tuple[int, int]]] = None

    @property
    def full_name(self):
        name = self._get_parent_attr_name()
        pulse_emitter = self._get_referenced_value(":../../")
        return f"{pulse_emitter.name}${name}"

    @property
    def pulse_name(self):
        return f"{self.full_name}$pulse"

    @property
    def waveform_name(self):
        return f"{self.full_name}$wf"

    @property
    def digital_marker_name(self):
        return f"{self.full_name}$dm"

    def _get_waveform_kwargs(self, waveform_function: Callable = None):
        if waveform_function is None:
            waveform_function = self.waveform_function

        return {
            attr: getattr(self, attr)
            for attr in inspect.signature(waveform_function).parameters.keys()
            if attr not in ["self", "operation", "args", "kwargs"]
        }

    def calculate_integration_weights(self) -> Dict[str, np.ndarray]:
        # Do nothing by default, allow subclasses to add integration weights
        ...

    def calculate_waveform(self):
        kwargs = self._get_waveform_kwargs()
        waveform = self.waveform_function(**kwargs)

        # Optionally convert IQ waveforms to complex waveform
        if isinstance(waveform, tuple) and len(waveform) == 2:
            if isinstance(waveform[0], (list, np.ndarray)):
                waveform = np.array(waveform[0]) + 1.0j * np.array(waveform[1])
            else:
                waveform = waveform[0] + 1.0j * waveform[1]

        return waveform

    @staticmethod
    def waveform_function(**kwargs) -> List[Union[float, complex]]:
        """Function that returns the waveform of the pulse.

        Can be either a list of floats, a list of complex numbers, or a tuple of two
        lists.
        This function is called from `calculate_waveform` with the kwargs of the
        dataclass instance as arguments. Each kwarg should therefore correspond to a
        dataclass field.
        """
        raise NotImplementedError("Subclass pulses should implement this method")

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

        for suffix, waveform in waveforms.items():
            waveform_name = self.waveform_name
            if suffix != "single":
                waveform_name += f"${suffix}"

            sample_label = "sample" if wf_type == "constant" else "samples"

            config["waveforms"][waveform_name] = {
                "type": wf_type,
                sample_label: waveform,
            }
            pulse_config["waveforms"][suffix] = waveform_name

    def _config_add_digital_markers(self, config):
        pulse_config = config["pulses"][self.pulse_name]
        config["digital_waveforms"][self.digital_marker_name] = {
            "samples": self.digital_marker
        }
        pulse_config["digital_marker"] = self.digital_marker_name

    def apply_to_config(self, config: dict) -> None:
        self._config_add_pulse(config)
        self._config_add_waveforms(config)

        if self.digital_marker:
            self._config_add_digital_markers(config)


@dataclass(kw_only=True, eq=False)
class ReadoutPulse(Pulse):
    amplitude: float
    rotation_angle: float = None

    operation: ClassVar[str] = "measurement"
    digital_marker: str = "ON"

    def calculate_integration_weights(self):
        integration_weights = {
            "cosine": {
                "cosine": [(1.0, self.length)],
                "sine": [(0.0, self.length)],
            },
            "sine": {
                "cosine": [(0.0, self.length)],
                "sine": [(1.0, self.length)],
            },
            # Why is there no minus cosine?
            "minus_sine": {
                "cosine": [(0.0, self.length)],
                "sine": [(-1.0, self.length)],
            },
        }
        if self.rotation_angle is not None:
            integration_weights["rotated_cosine"] = {
                "cosine": [(np.cos(self.rotation_angle), self.length)],
                "sine": [(-np.sin(self.rotation_angle), self.length)],
            }
            integration_weights["rotated_sine"] = {
                "cosine": [(np.sin(self.rotation_angle), self.length)],
                "sine": [(np.cos(self.rotation_angle), self.length)],
            }
            integration_weights["rotated_minus_sine"] = {
                "cosine": [(-np.sin(self.rotation_angle), self.length)],
                "sine": [(-np.cos(self.rotation_angle), self.length)],
            }
        return integration_weights

    def waveform_function(self, amplitude):
        # This should probably be complex because the pulse needs I and Q
        return complex(amplitude)


@dataclass(kw_only=True, eq=False)
class DragPulse(Pulse):
    rotation_angle: float
    amplitude: float
    sigma: float
    alpha: float
    anharmonicity: float
    detuning: float = 0.0
    subtracted: bool = True

    @staticmethod
    def waveform_function(
        length,
        amplitude,
        sigma,
        alpha,
        anharmonicity,
        detuning,
        subtracted,
        rotation_angle,
    ):
        from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

        I, Q = drag_gaussian_pulse_waveforms(
            amplitude=amplitude,
            length=length,
            sigma=sigma,
            alpha=alpha,
            anharmonicity=anharmonicity,
            detuning=detuning,
            subtracted=subtracted,
        )
        I, Q = np.array(I), np.array(Q)

        rotation_angle_rad = np.pi * rotation_angle / 180
        I_rot = I * np.cos(rotation_angle_rad) - Q * np.sin(rotation_angle_rad)
        Q_rot = I * np.sin(rotation_angle_rad) + Q * np.cos(rotation_angle_rad)

        return I_rot + 1.0j * Q_rot


@dataclass
class SquarePulse(Pulse):
    amplitude: float

    @staticmethod
    def waveform_function(amplitude):
        return amplitude


@dataclass
class GaussianPulse(Pulse):
    amplitude: float
    length: int
    sigma: float
    subtracted: bool = True

    @staticmethod
    def waveform_function(
        amplitude,
        length,
        sigma,
        subtracted=True,
    ):
        t = np.arange(length, dtype=int)
        center = (length - 1) / 2
        gauss_wave = amplitude * np.exp(-((t - center) ** 2) / (2 * sigma**2))

        if subtracted:
            gauss_wave = gauss_wave - gauss_wave[-1]
        return gauss_wave
