from dataclasses import dataclass
from typing import Callable, Dict, List, ClassVar
import inspect
import numpy as np

from quam_components.core import QuamComponent


__all__ = ["Pulse", "DragPulse"]


@dataclass(kw_only=True, eq=False)
class Pulse(QuamComponent):
    operation: ClassVar[str] = "control"
    length: int

    digital_marker: str = None

    def get_pulse_config(self):
        assert self.operation in ["control", "measurement"]
        assert isinstance(self.length, int)

        pulse_config = {
            "operation": self.operation,
            "length": self.length,
            "waveforms": {},
        }
        if self.digital_marker is not None:
            pulse_config["digital_marker"] = self.digital_marker

        return pulse_config

    def _get_waveform_kwargs(self, waveform_function: Callable = None):
        if waveform_function is None:
            waveform_function = self.waveform_function

        return {
            attr: getattr(self, attr)
            for attr in inspect.signature(waveform_function).parameters.keys()
            if attr not in ["self", "operation", "args", "kwargs"]
        }

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
    def waveform_function(**kwargs):
        raise NotImplementedError


@dataclass
class MeasurementPulse(Pulse):
    operation: ClassVar[str] = "measurement"

    integration_weights: str = None

    def get_pulse_config(self):
        pulse_config = super().get_pulse_config()
        if self.integration_weights is not None:
            pulse_config["integration_weights"] = self.integration_weights


@dataclass(kw_only=True, eq=False)
class DragPulse(Pulse):
    amplitude: float
    sigma: float
    alpha: float
    anharmonicity: float
    detuning: float = 0.0
    subtracted: bool = True

    from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

    waveform_function: ClassVar = staticmethod(drag_gaussian_pulse_waveforms)
