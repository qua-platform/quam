from typing import Any, ClassVar, Dict, Literal

from quam.components.ports.base_ports import OPXPlusPort
from quam.core import quam_dataclass


__all__ = ["OPXPlusDigitalInputPort"]


@quam_dataclass
class OPXPlusDigitalInputPort(OPXPlusPort):
    port_type: ClassVar[str] = "digital_input"

    deadtime: int = 4
    polarity: Literal["rising", "falling"] = "rising"
    threshold: float = 2.0
    shareable: bool = False

    def get_port_properties(self) -> Dict[str, Any]:
        return {
            "deadtime": self.deadtime,
            "polarity": self.polarity,
            "threshold": self.threshold,
            "shareable": self.shareable,
        }
