import warnings
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Tuple, Union

from quam.core import QuamComponent, quam_dataclass


__all__ = ["BasePort", "OPXPlusPort", "FEMPort"]


@quam_dataclass
class BasePort(QuamComponent, ABC):
    port_type: ClassVar[str]
    controller_name: str
    port_number: int

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
    def port_id(self) -> Union[Tuple[str, int], Tuple[str, int, int]]:
        pass

    def _update_port_config(self, port_config, port_properties):
        for key, value in port_properties.items():
            try:
                if key in port_config and value != port_config[key]:
                    warnings.warn(
                        f"Error generating QUA config: Controller {self.port_type} "
                        f"port {self.port_id} already has entry for {key}. This likely "
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
class OPXPlusPort(BasePort, ABC):

    def get_port_config(
        self, config: Dict[str, Any], create: bool = True
    ) -> Dict[str, Any]:

        if not create:
            try:
                controller_cfg = config["controllers"][self.controller_name]
                return controller_cfg[f"{self.port_type}"][self.port_number]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {self.controller_name} does "
                    f"not have entry {self.port_type}s for port {self.port_id}"
                )

        controller_cfg = config["controllers"].setdefault(self.controller_name, {})
        ports_cfg = controller_cfg.setdefault(f"{self.port_type}s", {})
        port_cfg = ports_cfg.setdefault(self.port_number, {})
        return port_cfg


@quam_dataclass
class FEMPort(BasePort, ABC):
    controller_name: str
    fem_number: int
    port_number: int

    def get_port_config(
        self, config: Dict[str, Any], create: bool = True
    ) -> Dict[str, Any]:

        if not create:
            try:
                controller_cfg = config["controllers"][self.controller_name]
                fem_cfg = controller_cfg["fems"][self.fem_number]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {self.controller_name} does "
                    f"not have entry for FEM {self.fem_number} for "
                    f"port {self.port_number}"
                )
            try:
                return fem_cfg[f"{self.port_type}s"][self.port_number]
            except KeyError:
                raise KeyError(
                    f"Error generating config: controller {self.controller_name} does "
                    f"not have entry {self.port_type}s for port {self.port_id}"
                )

        controller_cfg = config["controllers"].setdefault(self.controller_name, {})
        fems_cfg = controller_cfg.setdefault("fems", {})
        fem_cfg = fems_cfg.setdefault(self.fem_number, {})
        ports_cfg = fem_cfg.setdefault(f"{self.port_type}s", {})
        port_cfg = ports_cfg.setdefault(self.port_number, {})
        return port_cfg
