from typing import Any, Callable, Optional, Type, get_origin, get_args, TypeVar
import inspect
from typing import get_type_hints
from dataclasses import dataclass, field
import keyword

from quam.components import QuantumComponent


__all__ = ["FunctionProperties"]


QC = TypeVar("QC", bound=QuantumComponent)


@dataclass
class FunctionProperties:
    """
    Properties of a quantum operation function.

    This class extracts and stores metadata about functions that operate on
    quantum components, including argument information and type requirements.

    Attributes:
        quantum_component_name: Name of the parameter accepting the quantum component
        quantum_component_type: Type of quantum component the function operates on
        name: Name of the function
        required_args: List of required argument names after the quantum component
        optional_args: Dictionary of optional arguments and their default values
    """

    quantum_component_name: str
    quantum_component_type: Type[QC]
    name: str = ""
    required_args: list[str] = field(default_factory=list)
    optional_args: dict[str, Any] = field(default_factory=dict)
    return_type: Optional[Type] = None

    def __post_init__(self):
        # Make a new list/dict to avoid sharing between instances
        self.required_args = list(self.required_args)
        self.optional_args = dict(self.optional_args)

        # Validate argument names
        all_args = self.required_args + list(self.optional_args)
        for arg in all_args:
            if not arg.isidentifier():
                raise ValueError(f"Invalid argument name: {arg!r}")
            if keyword.iskeyword(arg):
                raise ValueError(f"Argument name cannot be a Python keyword: {arg!r}")

    @staticmethod
    def _is_quantum_component_type(type_hint: Optional[Type]) -> bool:
        """Check if type is or inherits from QuantumComponent."""
        try:
            return (
                type_hint is not None
                and isinstance(type_hint, type)
                and issubclass(type_hint, QuantumComponent)
            )
        except TypeError:
            return False

    @classmethod
    def from_function(cls, func: Callable) -> "FunctionProperties":
        if not callable(func):
            raise ValueError(f"Input {func!r} must be a callable")

        signature = inspect.signature(func)
        parameters = signature.parameters

        if not parameters:
            raise ValueError(
                f"Operation {func.__name__!r} must accept at least one argument "
                "(a QuantumComponent)"
            )

        # Try to get type hints, gracefully handle missing annotations
        try:
            type_hints = get_type_hints(func)
        except (NameError, TypeError):
            # Fallback to using the raw annotations if get_type_hints fails
            type_hints = getattr(func, "__annotations__", {})

        parameters_iterator = iter(parameters)
        first_param_name = next(parameters_iterator)

        # Get and resolve the type of the first parameter
        first_param_type = type_hints.get(first_param_name)

        if not cls._is_quantum_component_type(first_param_type):
            if first_param_type is None:
                msg = (
                    f"Operation {func.__name__!r} is missing type annotation for "
                    f"first parameter {first_param_name!r}"
                )
            else:
                msg = (
                    f"Operation {func.__name__!r} must accept a QuantumComponent "
                    f"as its first argument, got {first_param_type!r}"
                )
            raise ValueError(msg)

        function_properties = cls(
            quantum_component_name=first_param_name,
            quantum_component_type=first_param_type,  # type: ignore
            name=func.__name__,
        )

        # Process remaining parameters
        for param_name in parameters_iterator:
            param = parameters[param_name]
            if param.default == inspect.Parameter.empty:
                function_properties.required_args.append(param_name)
            else:
                # Store the default value directly
                function_properties.optional_args[param_name] = param.default

        # Get the return type from the function annotations
        function_properties.return_type = type_hints.get("return")

        return function_properties
