from dataclasses import dataclass
from typing import Dict, List
import inspect
import numpy as np

from quam_components.core import QuamComponent


@dataclass(kw_only=True, eq=False)
class Pulse(QuamComponent):
    operation: str
    length: int

    integration_weights: Dict[str, List[float]] = None
    digital_marker: str = None

    def get_pulse_config(self):
        assert self.operation in ["control", "measurement"]
        assert isinstance(self.length, int)

        pulse_config = {
            "operation": self.operation,
            "length": self.length,
        }

        if self.operation == "measurement":
            # TODO Verify that these settings are optional
            if self.integration_weights is not None:
                pulse_config["integration_weights"] = self.integration_weights
            if self.digital_marker is not None:
                pulse_config["digital_marker"] = self.digital_marker

        return pulse_config

    def calculate_waveform(self):
        arg_names = inspect.signature(self.waveform_function).parameters.keys()
        if arg_names[0] == "self":
            arg_names = arg_names[1:]

        kwargs = {attr: getattr(self, attr) for attr in arg_names}
        waveform = self.waveform_function(**kwargs)

        # Optionally convert IQ waveforms to complex waveform
        if isinstance(waveform, tuple) and len(waveform) == 2:
            if isinstance(waveform[0], (list, np.ndarray)):
                waveform = np.array(waveform[0]) + 1.0j * np.array(waveform[1])
            else:
                waveform = waveform[0] + 1.0j * waveform[1]

        return waveform

    def waveform_function(self, **kwargs):
        raise NotImplementedError


@dataclass(kw_only=True, eq=False)
class DragPulse(Pulse):
    amplitude: float
    sigma: float
    alpha: float
    anharmonicity: float
    detuning: float = 0.0
    subtracted: bool = True

    from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

    waveform_function = drag_gaussian_pulse_waveforms
