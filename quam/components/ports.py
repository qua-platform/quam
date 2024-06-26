from dataclasses import field
from typing import Dict, List, Literal, Optional, Tuple
from quam.core import QuamComponent, quam_dataclass


@quam_dataclass
class OPXPlusAnalogOutputPort(QuamComponent):
    port: Tuple[str, int]
    offset: float = 0.0
    delay: int = 0
    crosstalk: Dict[int, float] = field(default_factory=dict)
    feedforward_filter: List[float] = field(default_factory=list)
    feedback_filter: List[float] = field(default_factory=list)
    shareable: bool = False


@quam_dataclass
class OPXPlusAnalogInputPort(QuamComponent):
    port: Tuple[str, int]
    offset: float = 0.0
    gain_db: int = 0
    shareable: bool = False


@quam_dataclass
class OPXPlusDigitalOutputPort(QuamComponent):
    port: Tuple[str, int]
    inverted: bool = False
    shareable: bool = False


@quam_dataclass
class OPXPlusDigitalInputPort(QuamComponent):
    port: Tuple[str, int]
    deadtime: int = 4
    polarity: Literal["Rising", "Falling"] = "Rising"
    threshold: float = 2.0
    shareable: bool = False


@quam_dataclass
class LFFEMAnalogOutputPort(QuamComponent):
    port: Tuple[str, int]
    offset: float = 0.0
    delay: int = 0
    crosstalk: Dict[int, float] = field(default_factory=dict)
    feedforward_filter: List[float] = field(default_factory=list)
    feedback_filter: List[float] = field(default_factory=list)
    shareable: bool = False
    sampling_rate: float = 1e9  # Either 1e9 or 2e9
    upsampling_mode: Literal["mw", "pulse"] = "mw"
    output_mode: Literal["direct", "amplified"] = "direct"


@quam_dataclass
class LFFEMAnalogInputPort(QuamComponent):
    port: Tuple[str, int]
    offset: float = 0.0
    gain_db: int = 0
    shareable: bool = False
    sampling_rate: float = 1e9  # Either 1e9 or 2e9


@quam_dataclass
class LFFEMDigitalOutputPort(QuamComponent):
    port: Tuple[str, int]
    level: Literal["TTL", "LVTTL"] = "LVTTL"
    inverted: bool = False
    shareable: bool = False


@quam_dataclass
class MWFEMAnalogOutputPort(QuamComponent):
    port: Tuple[str, int]
    band: int
    upconverter_frequency: Optional[float] = None
    upconverters: Optional[Dict[int, float]] = None
    delay: int = 0
    shareable: bool = False
    sampling_rate: float = 1e9  # Either 1e9 or 2e9
    full_scale_power_dbm: int = -11


@quam_dataclass
class MWFEMAnalogInputPort(QuamComponent):
    port: Tuple[str, int]
    band: int
    downconverter_frequency: float
    sampling_rate: float = 1e9  # Either 1e9 or 2e9
    shareable: bool = False


@quam_dataclass
class MWFEMDigitalOutputPort(QuamComponent):
    port: Tuple[str, int]
    level: Literal["TTL", "LVTTL"] = "LVTTL"
    inverted: bool = False
    shareable: bool = False
