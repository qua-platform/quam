from collections import UserDict
import functools
from typing import Callable


class OperationsRegistry(UserDict):
    """A registry to store and manage operations."""

    def register_operation(self, func: Callable) -> Callable:
        """
        Register a function as an operation.

        This method stores the function in the operations dictionary and returns a wrapped version of the function
        that maintains the original function's signature and docstring.

        Args:
            func (callable): The function to register as an operation.

        Returns:
            callable: The wrapped function.
        """

        @functools.wraps(func)
        def wrapped_operation(*args, **kwargs):
            """Call the registered operation with the provided arguments."""
            return func(*args, **kwargs)

        self[func.__name__] = wrapped_operation

        return wrapped_operation
