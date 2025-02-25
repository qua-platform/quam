import warnings
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Tuple, Union

from quam.core import QuamComponent, quam_dataclass


__all__ = ["BasePort", "OPXPlusPort", "FEMPort"]


@quam_dataclass
class BasePort(QuamComponent, ABC):
    port_type: ClassVar[str]

    @abstractmethod
    def get_port_config(
        self, config: Dict[str, Any], create: bool = True
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_port_properties(self) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def port_tuple(self) -> Union[Tuple[str, int], Tuple[str, int, int]]:
        pass

    def _update_port_config(self, port_config, port_properties):
        for key, value in port_properties.items():
            try:
                if key in port_config and value != port_config[key]:
                    warnings.warn(
                        f"Error generating QUA config: Controller {self.port_type} "
                        f"port {self.port_tuple} already has entry for {key}. This "
                        f"likely means that the port is being configured multiple "
                        f"times. Overwriting {port_config[key]} → {value}."
                    )
            except Exception:
                pass
            port_config[key] = value

    def apply_to_config(self, config: Dict) -> None:
        super().apply_to_config(config)

        port_cfg = self.get_port_config(config)
        port_properties = self.get_port_properties()
        self._update_port_config(port_cfg, port_properties)


@quam_dataclass(kw_only=False)
class OPXPlusPort(BasePort, ABC):
    controller_id: Union[str, int]
    port_id: int

    @property
    def port_tuple(self) -> Tuple[Union[str, int], int]:
        return self.controller_id, self.port_id

    def get_port_config(
        self, config: Dict[str, Any], create: bool = True
    ) -> Dict[str, Any]:

        if not create:
            try:
                controller_cfg = config["controllers"][self.controller_id]
                return controller_cfg[f"{self.port_type}"][self.port_id]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {self.controller_id} does "
                    f"not have entry {self.port_type}s for port {self.port_tuple}"
                )

        controller_cfg = config["controllers"].setdefault(self.controller_id, {})
        ports_cfg = controller_cfg.setdefault(f"{self.port_type}s", {})
        port_cfg = ports_cfg.setdefault(self.port_id, {})
        return port_cfg


@quam_dataclass(kw_only=False)
class FEMPort(BasePort, ABC):
    fem_type: ClassVar[str]
    controller_id: Union[str, int]
    fem_id: int
    port_id: int

    @property
    def port_tuple(self) -> Tuple[Union[str, int], int, int]:
        return self.controller_id, self.fem_id, self.port_id

    def get_port_config(
        self, config: Dict[str, Any], create: bool = True
    ) -> Dict[str, Any]:

        if not create:
            try:
                controller_cfg = config["controllers"][self.controller_id]
                fem_cfg = controller_cfg["fems"][self.fem_id]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {self.controller_id} does "
                    f"not have entry for FEM {self.fem_id} for "
                    f"port {self.port_id}"
                )
            try:
                return fem_cfg[f"{self.port_type}s"][self.port_id]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {self.controller_id} does "
                    f"not have entry {self.port_type}s for port {self.port_tuple}"
                )

        controller_cfg = config["controllers"].setdefault(self.controller_id, {})
        fems_cfg = controller_cfg.setdefault("fems", {})
        fem_cfg = fems_cfg.setdefault(self.fem_id, {})
        if hasattr(self, "fem_type"):
            if fem_cfg.get("type", self.fem_type) != self.fem_type:
                raise ValueError(
                    f"Error generating config: FEM {self.fem_id} is not of type "
                    f"{self.fem_type}"
                )
            fem_cfg["type"] = self.fem_type

        ports_cfg = fem_cfg.setdefault(f"{self.port_type}s", {})
        port_cfg = ports_cfg.setdefault(self.port_id, {})
        return port_cfg
