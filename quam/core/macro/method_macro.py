from typing import Any, Callable, TypeVar
import functools

from quam.core.macro.base_macro import BaseMacro


__all__ = ["method_macro", "MethodMacro"]


T = TypeVar("T", bound=Callable)


class MethodMacro(BaseMacro):
    """Decorator that marks methods which should be exposed as macros."""

    def __init__(self, func: T) -> None:
        functools.wraps(func)(self)
        self.func = func
        self.instance = None

    def __get__(self, instance, owner):
        # Store the instance to which this method is bound
        self.instance = instance
        return self

    def apply(self, *args, **kwargs) -> Any:
        """Implements BaseMacro.apply by calling the wrapped function"""
        if self.instance is not None:
            # Call the function with the instance as the first argument
            return self.func(self.instance, *args, **kwargs)
        return self.func(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if args and args[0] is self.instance:
            args = args[1:]
        return self.apply(*args, **kwargs)

    @staticmethod
    def is_macro_method(obj: Any) -> bool:
        return isinstance(obj, MethodMacro)


# Lower-case alias for MethodMacro for more pythonic decorator
method_macro = MethodMacro
