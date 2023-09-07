from dataclasses import dataclass
from quam_components.core import QuamComponent

@dataclass(kw_only=True, eq=False)
class Pulse(QuamComponent):
    def apply_to_config(self, config: dict) -> None:
        # Add waveform(s)

        # Add pulse
        # Should have a unique name
        ...