from abc import ABC, abstractmethod
from dataclasses import field
from typing import Any, Dict, Union
from quam.core.quam_classes import quam_dataclass, QuamComponent
from quam.components.operations import BaseOperation

__all__ = ["QuantumComponent"]


@quam_dataclass
class QuantumComponent(QuamComponent, ABC):
    id: Union[str, int]
    operations: Dict[str, BaseOperation] = field(default_factory=dict)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def __call__(self):
        self.execute()

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        pass
