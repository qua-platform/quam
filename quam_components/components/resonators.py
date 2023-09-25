from typing import Union
from dataclasses import dataclass

from quam_components.core import patch_dataclass

from .general import Mixer, PulseEmitter

patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10


__all__ = ["ReadoutResonator"]


@dataclass(kw_only=True, eq=False)
class ReadoutResonator(PulseEmitter):
    id: Union[int, str]
    mixer: Mixer

    frequency: float = None

    time_of_flight: int = 24
    smearing: int = 0

    controller: str = "con1"

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"res{self.id}"

    def apply_to_config(self, config: dict):
        # Add pulses & waveforms
        super().apply_to_config(config)

        config["elements"][self.name] = {
            "mixInputs": self.mixer.get_input_config(),
            "intermediate_frequency": self.mixer.intermediate_frequency,
            "operations": self.pulse_mapping,
            "outputs": {  # TODO should this be hardcoded?
                "out1": (self.controller, 1),
                "out2": (self.controller, 2),
            },
            "smearing": self.smearing,
            "time_of_flight": self.time_of_flight,
        }
