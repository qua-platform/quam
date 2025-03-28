from abc import ABC, abstractmethod
from dataclasses import field
import inspect
from typing import Any, Callable, Dict, Union, TypeVar, cast
from quam.core.quam_classes import quam_dataclass, QuamComponent
from quam.core.macro import BaseMacro, method_macro

__all__ = ["QuantumComponent"]


T = TypeVar("T", bound=Callable)


@quam_dataclass
class QuantumComponent(QuamComponent, ABC):
    id: Union[str, int]
    macros: Dict[str, BaseMacro] = field(default_factory=dict)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def apply(self, operation: str, *args, **kwargs) -> Any:
        operation_obj = self.get_macros()[operation]
        return operation_obj.apply(*args, **kwargs)

    @staticmethod
    def register_macro(func: T) -> T:
        """Decorator to register a method as a macro entry point"""
        return cast(T, method_macro(func))

    def _get_method_macros(self) -> Dict[str, method_macro]:
        return dict(
            inspect.getmembers(self, predicate=lambda x: isinstance(x, method_macro))
        )

    def get_macros(self) -> Dict[str, BaseMacro]:
        return {**self.macros, **self._get_method_macros()}
