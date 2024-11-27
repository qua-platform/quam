from abc import ABC, abstractmethod
from dataclasses import field
from typing import Any, Dict, Union
from quam.core.quam_classes import quam_dataclass, QuamComponent
from quam.components.implementations import BaseImplementation

__all__ = ["QuantumComponent"]


@quam_dataclass
class QuantumComponent(QuamComponent, ABC):
    id: Union[str, int]
    implementations: Dict[str, BaseImplementation] = field(default_factory=dict)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def apply(self, operation: str, *args, **kwargs) -> Any:
        operation_obj = self.implementations[operation]
        operation_obj.apply(*args, **kwargs)
