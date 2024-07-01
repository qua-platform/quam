from abc import ABC
from typing import Any, ClassVar, Dict, Literal

from quam.components.ports.base_ports import BasePort, FEMPort, OPXPlusPort
from quam.core import quam_dataclass


__all__ = ["DigitalOutputPort", "OPXPlusDigitalOutputPort", "FEMDigitalOutputPort"]


@quam_dataclass
class DigitalOutputPort(BasePort, ABC):
    port_type: ClassVar[str] = "digital_output"

    inverted: bool = False
    shareable: bool = False

    def get_port_properties(self) -> Dict[str, Any]:
        return {"inverted": self.inverted, "shareable": self.shareable}


@quam_dataclass
class OPXPlusDigitalOutputPort(DigitalOutputPort, OPXPlusPort):
    pass


@quam_dataclass
class FEMDigitalOutputPort(DigitalOutputPort, FEMPort):
    level: Literal["TTL", "LVTTL"] = "LVTTL"

    def get_port_properties(self) -> Dict[str, Any]:
        port_properties = super().get_port_properties()
        port_properties["level"] = self.level
        return port_properties
