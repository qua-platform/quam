from abc import ABC
from typing import Any, ClassVar, Dict, Optional

from quam.components.ports.base_ports import BasePort, FEMPort, OPXPlusPort
from quam.core import quam_dataclass


__all__ = [
    "LFAnalogInputPort",
    "OPXPlusAnalogInputPort",
    "LFFEMAnalogInputPort",
    "MWFEMAnalogInputPort",
]


@quam_dataclass
class LFAnalogInputPort(BasePort, ABC):
    fem_type: ClassVar[str] = "LF"
    port_type: ClassVar[str] = "analog_input"

    offset: Optional[float] = None
    gain_db: int = 0
    shareable: bool = False

    def get_port_properties(self):
        port_cfg = {
            "gain_db": self.gain_db,
            "shareable": self.shareable,
        }
        if self.offset is not None:
            port_cfg["offset"] = self.offset
        return port_cfg


@quam_dataclass
class OPXPlusAnalogInputPort(LFAnalogInputPort, OPXPlusPort):
    pass


@quam_dataclass
class LFFEMAnalogInputPort(LFAnalogInputPort, FEMPort):
    sampling_rate: float = 1e9  # Either 1e9 or 2e9

    def get_port_properties(self) -> Dict[str, Any]:
        port_properties = super().get_port_properties()
        port_properties["sampling_rate"] = self.sampling_rate
        return port_properties


@quam_dataclass
class MWFEMAnalogInputPort(FEMPort):
    fem_type: ClassVar[str] = "MW"
    port_type: ClassVar[str] = "analog_input"

    band: int
    downconverter_frequency: float
    sampling_rate: float = 1e9  # Either 1e9 or 2e9
    shareable: bool = False

    def get_port_properties(self) -> Dict[str, Any]:
        return {
            "band": self.band,
            "downconverter_frequency": self.downconverter_frequency,
            "sampling_rate": self.sampling_rate,
            "shareable": self.shareable,
        }
