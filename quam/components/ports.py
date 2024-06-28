from abc import ABC, abstractmethod
from dataclasses import field
from typing import Any, ClassVar, Dict, List, Literal, Optional, Tuple, Union
import warnings
from quam.core import QuamComponent, quam_dataclass


# ---- General ports ---- #
@quam_dataclass
class Port(QuamComponent, ABC):
    port_type: ClassVar[str]
    port: Union[Tuple[str, int], Tuple[str, int, int]]

    @abstractmethod
    def get_port_config(
        self, config: Dict[str, Any], create: bool = True
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_port_properties(self) -> Dict[str, Any]:
        pass

    @staticmethod
    def _update_port_config(port_config, port_properties):
        for key, value in port_properties.items():
            try:
                if key in port_config and value != port_config[key]:
                    warnings.warn(
                        f"Error generating QUA config: Controller {self.port_type} "
                        f"port {self.port} already has entry for {key}. This likely "
                        f"means that the port is being configured multiple times. "
                        f"Overwriting {port_config['key']} → {value}."
                    )
            except Exception:
                pass
            port_config[key] = value

    def apply_to_config(self, config: Dict) -> None:
        super().apply_to_config(config)

        port_cfg = self.get_port_config(config)
        port_properties = self.get_port_properties()
        self._update_port_config(port_cfg, port_properties)


@quam_dataclass
class OPXPlusPort(Port, ABC):
    port: Tuple[str, int]

    def get_port_config(
        self, config: Dict[str, Any], create: bool = True
    ) -> Dict[str, Any]:
        controller_name, port = self.port

        if not create:
            try:
                return config["controllers"][controller_name][f"{self.port_type}"][port]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {controller_name} does not "
                    f"have entry {self.port_type}s for port {self.port}"
                )

        controller_cfg = config["controllers"].setdefault(controller_name, {})
        ports_cfg = controller_cfg.setdefault(f"{self.port_type}s", {})
        port_cfg = ports_cfg.setdefault(port, {})
        return port_cfg


@quam_dataclass
class FEMPort(Port, ABC):
    port: Tuple[str, int, int]

    def get_port_config(
        self, config: Dict[str, Any], create: bool = True
    ) -> Dict[str, Any]:
        controller_name, fem, port = self.port

        if not create:
            try:
                fem_cfg = config["controllers"][controller_name]["fems"][fem]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {controller_name} does not "
                    f"have entry for FEM {fem} for port {self.port}"
                )
            try:
                return fem_cfg[f"{self.port_type}s"][port]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {controller_name} does not "
                    f"have entry {self.port_type}s for port {self.port}"
                )

        controller_cfg = config["controllers"].setdefault(controller_name, {})
        ports_cfg = controller_cfg.setdefault(f"{self.port_type}s", {})
        port_cfg = ports_cfg.setdefault(port, {})
        return port_cfg


# --- Analog ports --- #
@quam_dataclass
class LFAnalogOutputPort(QuamComponent, ABC):
    port_type: ClassVar[str] = "analog_output"

    offset: float = 0.0
    delay: int = 0
    crosstalk: Dict[int, float] = field(default_factory=dict)
    feedforward_filter: List[float] = field(default_factory=list)
    feedback_filter: List[float] = field(default_factory=list)
    shareable: bool = False

    def get_port_properties(self):
        return {
            "offset": self.offset,
            "delay": self.delay,
            "crosstalk": self.crosstalk,
            "feedforward_filter": self.feedforward_filter,
            "feedback_filter": self.feedback_filter,
            "shareable": self.shareable,
        }


@quam_dataclass
class LFAnalogInputPort(QuamComponent, ABC):
    port_type: ClassVar[str] = "analog_input"

    offset: float = 0.0
    gain_db: int = 0
    shareable: bool = False

    def get_port_properties(self):
        return {
            "offset": self.offset,
            "gain_db": self.gain_db,
            "shareable": self.shareable,
        }


@quam_dataclass
class OPXPlusAnalogOutputPort(LFAnalogOutputPort, OPXPlusPort):
    pass


@quam_dataclass
class OPXPlusAnalogInputPort(LFAnalogInputPort, OPXPlusPort):
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
class LFFEMAnalogInputPort(LFAnalogInputPort, FEMPort):
    sampling_rate: float = 1e9  # Either 1e9 or 2e9

    def get_port_properties(self) -> Dict[str, Any]:
        port_properties = super().get_port_properties()
        port_properties["sampling_rate"] = self.sampling_rate
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
        return {
            "band": self.band,
            "upconverter_frequency": self.upconverter_frequency,
            "upconverters": self.upconverters,
            "delay": self.delay,
            "shareable": self.shareable,
            "sampling_rate": self.sampling_rate,
            "full_scale_power_dbm": self.full_scale_power_dbm,
        }


@quam_dataclass
class MWFEMAnalogInputPort(FEMPort):
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


# --- Digital ports --- #
@quam_dataclass
class DigitalOutputPort(QuamComponent, ABC):
    port_type: ClassVar[str] = "digital_output"

    inverted: bool = False
    shareable: bool = False

    def get_port_properties(self) -> Dict[str, Any]:
        return {"inverted": self.inverted, "shareable": self.shareable}


@quam_dataclass
class OPXPlusDigitalOutputPort(DigitalOutputPort, OPXPlusPort):
    pass


@quam_dataclass
class OPXPlusDigitalInputPort(OPXPlusPort):
    deadtime: int = 4
    polarity: Literal["Rising", "Falling"] = "Rising"
    threshold: float = 2.0
    shareable: bool = False

    def get_port_properties(self) -> Dict[str, Any]:
        return {
            "deadtime": self.deadtime,
            "polarity": self.polarity,
            "threshold": self.threshold,
            "shareable": self.shareable,
        }


@quam_dataclass
class FEMDigitalOutputPort(DigitalOutputPort, FEMPort):
    level: Literal["TTL", "LVTTL"] = "LVTTL"

    def get_port_properties(self) -> Dict[str, Any]:
        port_properties = super().get_port_properties()
        port_properties["level"] = self.level
        return port_properties
