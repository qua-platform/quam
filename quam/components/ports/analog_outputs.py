from abc import ABC
from dataclasses import field
from typing import Any, ClassVar, Dict, List, Literal, Optional

from quam.components.ports.base_ports import BasePort, FEMPort, OPXPlusPort
from quam.core import quam_dataclass


__all__ = [
    "LFAnalogOutputPort",
    "OPXPlusAnalogOutputPort",
    "LFFEMAnalogOutputPort",
    "MWFEMAnalogOutputPort",
]


@quam_dataclass
class LFAnalogOutputPort(BasePort, ABC):
    port_type: ClassVar[str] = "analog_output"

    offset: float = 0.0
    delay: int = 0
    crosstalk: Dict[int, float] = field(default_factory=dict)
    feedforward_filter: List[float] = field(default_factory=list)
    feedback_filter: List[float] = field(default_factory=list)
    shareable: bool = False

    def get_port_properties(self):
        port_properties = {
            "delay": self.delay,
            "crosstalk": self.crosstalk,
            "feedforward_filter": self.feedforward_filter,
            "feedback_filter": self.feedback_filter,
            "shareable": self.shareable,
        }
        if self.offset is not None:
            port_properties["offset"] = self.offset
        return port_properties


@quam_dataclass
class OPXPlusAnalogOutputPort(LFAnalogOutputPort, OPXPlusPort):
    pass


@quam_dataclass
class LFFEMAnalogOutputPort(LFAnalogOutputPort, FEMPort):
    sampling_rate: float = 1e9  # Either 1e9 or 2e9
    upsampling_mode: Literal["mw", "pulse"] = "mw"
    output_mode: Literal["direct", "amplified"] = "direct"

    def get_port_properties(self) -> Dict[str, Any]:
        port_properties = super().get_port_properties()
        port_properties["sampling_rate"] = self.sampling_rate
        port_properties["upsampling_mode"] = self.upsampling_mode
        port_properties["output_mode"] = self.output_mode
        return port_properties


@quam_dataclass
class MWFEMAnalogOutputPort(FEMPort):
    port_type: ClassVar[str] = "analog_output"

    band: int
    upconverter_frequency: Optional[float] = None
    upconverters: Optional[Dict[int, float]] = None
    delay: int = 0
    shareable: bool = False
    sampling_rate: float = 1e9  # Either 1e9 or 2e9
    full_scale_power_dbm: int = -11

    def get_port_properties(self) -> Dict[str, Any]:
        port_cfg = {
            "band": self.band,
            "delay": self.delay,
            "shareable": self.shareable,
            "sampling_rate": self.sampling_rate,
            "full_scale_power_dbm": self.full_scale_power_dbm,
        }
        if self.upconverter_frequency is not None:
            port_cfg["upconverter_frequency"] = self.upconverter_frequency
        if self.upconverters is not None:
            port_cfg["upconverters"] = self.upconverters
        return port_cfg
