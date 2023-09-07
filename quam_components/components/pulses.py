from dataclasses import dataclass
from typing import Dict, List, ClassVar
from quam_components.core import QuamComponent


@dataclass(kw_only=True, eq=False)
class Pulse(QuamComponent):
    operation: str
    length: int

    integration_weights: Dict[str, List[float]] = None
    digital_marker: str = None

    waveform_properties: ClassVar[List[str]]

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
        kwargs = {attr: getattr(self, attr) for attr in self.waveform_properties}
        return self.waveform_function(**kwargs)

    def waveform_function(self, **kwargs):
        raise NotImplementedError
