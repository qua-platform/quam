from collections import UserDict
import functools
from typing import Callable, Optional, TypeVar, Any

from quam.core.operation import Operation


__all__ = ["OperationsRegistry"]

T = TypeVar("T", bound=Callable[..., Any])


class OperationsRegistry(UserDict):
    """A registry to store and manage operations."""

    def register_operation(self, func: Optional[T] = None, unitary=None) -> T:
        """
        Register a function as an operation.

        This method stores the function in the operations dictionary and returns a
        wrapped version of the function that maintains the original function's
        signature and docstring.

        Args:
            func (callable): The function to register as an operation.

        Returns:
            callable: The wrapped function.
        """
        if func is None:
            return functools.partial(self.register_operation, unitary=unitary)

        operation = Operation(func, unitary=unitary)
        operation = functools.update_wrapper(operation, func)

        self[func.__name__] = operation

        return operation  # type: ignore
