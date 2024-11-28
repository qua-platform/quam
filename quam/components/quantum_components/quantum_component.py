from abc import ABC, abstractmethod
from dataclasses import field
from typing import Any, Dict, Union
from quam.core.quam_classes import quam_dataclass, QuamComponent
from quam.components.macro import QuamMacro

__all__ = ["QuantumComponent"]


@quam_dataclass
class QuantumComponent(QuamComponent, ABC):
    id: Union[str, int]
    macros: Dict[str, QuamMacro] = field(default_factory=dict)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def apply(self, operation: str, *args, **kwargs) -> Any:
        operation_obj = self.macros[operation]
        operation_obj.apply(*args, **kwargs)
