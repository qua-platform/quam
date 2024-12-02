from typing import Callable

from quam.core.operation.function_properties import FunctionProperties
from quam.components import QuantumComponent


__all__ = ["Operation"]


class Operation:
    def __init__(self, func: Callable, unitary=None):
        self.func = func
        self.unitary = unitary
        self.properties = FunctionProperties.from_function(func)

    def get_macro(self, quantum_component: QuantumComponent):
        macros = quantum_component.get_macros()
        return macros[self.properties.name]

    def __call__(self, *args, **kwargs):
        if not args or not isinstance(args[0], QuantumComponent):
            if self.properties.quantum_component_type is not None:
                raise ValueError(
                    f"First argument to {self.properties.name} must be a "
                    f"{self.properties.quantum_component_type.__name__}"
                )

        quantum_component, *required_args = args

        macro = self.get_macro(quantum_component)
        return macro.apply(quantum_component, *required_args, **kwargs)
