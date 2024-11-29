from typing import Any, Callable, TypeVar
import functools

from quam.core.macro.base_macro import BaseMacro


__all__ = ["MethodMacro"]


T = TypeVar("T", bound=Callable)


class MethodMacro(BaseMacro):
    """Decorator that marks methods which should be exposed as macros."""

    def __init__(self, func: T) -> None:
        functools.wraps(func)(self)
        self.func = func

    def apply(self, *args, **kwargs) -> Any:
        """Implements BaseMacro.apply by calling the wrapped function"""
        return self.func(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)

    @staticmethod
    def is_macro_method(obj: Any) -> bool:
        return isinstance(obj, MethodMacro)
