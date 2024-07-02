from abc import ABC
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
    fem_type: ClassVar[str] = "LF"
    port_type: ClassVar[str] = "analog_output"

    offset: Optional[float] = None
    delay: int = 0
    crosstalk: Optional[Dict[int, float]] = None
    feedforward_filter: Optional[List[float]] = None
    feedback_filter: Optional[List[float]] = None
    shareable: bool = False

    def get_port_properties(self):
        port_properties = {
            "delay": self.delay,
            "shareable": self.shareable,
        }
        if self.crosstalk is not None:
            port_properties["crosstalk"] = self.crosstalk
        if self.feedforward_filter is not None:
            port_properties["feedforward_filter"] = list(self.feedforward_filter)
        if self.feedback_filter is not None:
            port_properties["feedback_filter"] = list(self.feedback_filter)
        if self.offset is not None:
            port_properties["offset"] = self.offset
        return port_properties


@quam_dataclass
class OPXPlusAnalogOutputPort(LFAnalogOutputPort, OPXPlusPort):
    pass


@quam_dataclass
class LFFEMAnalogOutputPort(LFAnalogOutputPort, FEMPort):
    fem_type: ClassVar[str] = "LF"
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
    fem_type: ClassVar[str] = "MW"
    port_type: ClassVar[str] = "analog_output"

    band: int
    upconverter_frequency: Optional[float] = None
    upconverters: Optional[Dict[int, float]] = None
    delay: int = 0
    shareable: bool = False
    sampling_rate: float = 1e9  # Either 1e9 or 2e9
    full_scale_power_dbm: int = -11

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.upconverter_frequency is None and self.upconverters is None:
            raise ValueError(
                "MWAnalogOutputPort: Either upconverter_frequency or upconverters must "
                "be provided"
            )

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
