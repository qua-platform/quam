# QUAM Macro API

Welcome to the QUAM Macro API Documentation.
The QUAM Macro module provides pre-built macro operations for common quantum gate sequences on qubits and qubit pairs.
Information can be found in [QUAM Gate-Level Operations Documentation](/features/gate-level-operations) in the User Guide.

This section provides detailed API references for macro operations—high-level functions that encapsulate common quantum operations and gate sequences—simplifying the implementation of complex quantum experiments.

!!! note "Advanced: Core Macro Infrastructure"
    For creating custom macro types or understanding the underlying macro system, see the core macro classes:

    - [BaseMacro][quam.core.macro.BaseMacro] - Base class for all macros
    - [QuamMacro][quam.core.macro.QuamMacro] - Base class for QUAM component macros
    - [method_macro][quam.core.macro.method_macro] - Decorator for exposing methods as macros

::: quam.components.macro
    options:
      members:
        - PulseMacro
        - QubitMacro
        - QubitPairMacro
