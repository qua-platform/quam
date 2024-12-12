from abc import ABC, abstractmethod
from typing import Any


__all__ = ["BaseMacro"]


class BaseMacro(ABC):
    """Base class for all macro types in the system"""

    @abstractmethod
    def apply(self, *args, **kwargs) -> Any:
        """Applies the macro operation"""
        pass
