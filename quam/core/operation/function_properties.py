from typing import Any, Callable
import inspect
from typing import get_type_hints
from dataclasses import dataclass, field

from quam.components import QuantumComponent


__all__ = ["FunctionProperties"]


@dataclass
class FunctionProperties:
    quantum_component_name: str
    quantum_component_type: type[QuantumComponent]
    name: str = ""
    required_args: list[str] = field(default_factory=list)
    optional_args: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_function(cls, func: Callable) -> "FunctionProperties":
        signature = inspect.signature(func)
        parameters = signature.parameters

        if not len(parameters):
            raise ValueError(
                f"Operation {func.__name__} must accept a QuantumComponent"
            )

        parameters_iterator = iter(parameters)

        # Get first parameter and check if it is a QuantumComponent
        first_param_name = next(parameters_iterator)
        first_param_type = get_type_hints(func).get(first_param_name, None)
        # First parameter must be a QuantumComponent
        if first_param_type and issubclass(first_param_type, QuantumComponent):
            function_properties = FunctionProperties(
                quantum_component_name=first_param_name,
                quantum_component_type=first_param_type,
                name=func.__name__,
            )
        else:
            raise ValueError(
                f"Operation {func.__name__} must accept a QuantumComponent as its"
                " first argument"
            )

        for param in parameters_iterator:
            param = parameters[param]
            if param.default == inspect.Parameter.empty:
                function_properties.required_args.append(param.name)
            else:
                function_properties.optional_args[param.name] = param.default

        return function_properties
