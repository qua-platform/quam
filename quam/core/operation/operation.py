from typing import Callable, Optional, Any

from quam.core.operation.function_properties import FunctionProperties
from quam.components import QuantumComponent


__all__ = ["Operation"]


class Operation:
    def __init__(self, func: Callable):
        """
        Initialize a quantum operation.

        This is typically used implicitly from the decorator @operations_registry.register_operation.

        Args:
            func: The function implementing the operation
        """
        self.func = func
        self.properties = FunctionProperties.from_function(func)

    def get_macro(self, quantum_component: QuantumComponent):
        """
        Get the macro implementation for this operation from a quantum component.

        Args:
            quantum_component: Component to get the macro from

        Returns:
            The macro implementation

        Raises:
            KeyError: If the macro is not implemented for this component
        """
        macros = quantum_component.get_macros()
        try:
            return macros[self.properties.name]
        except KeyError:
            raise KeyError(
                f"Operation '{self.properties.name}' is not implemented for "
                f"{quantum_component.__class__.__name__}"
            )

    def __call__(self, *args, **kwargs):
        """
        Execute the operation on a quantum component.

        Args:
            *args: Positional arguments, first must be a quantum component
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the macro execution

        Raises:
            ValueError: If first argument is not the correct quantum component type
        """
        if not args:
            raise ValueError(
                f"Operation {self.properties.name} requires at least one argument"
            )

        quantum_component = args[0]
        if not isinstance(quantum_component, self.properties.quantum_component_type):
            raise ValueError(
                f"First argument to {self.properties.name} must be a "
                f"{self.properties.quantum_component_type.__name__}, got "
                f"{type(quantum_component).__name__}"
            )

        quantum_component, *required_args = args
        macro = self.get_macro(quantum_component)
        return macro.apply(*required_args, **kwargs)
