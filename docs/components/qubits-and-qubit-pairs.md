# Qubits and Qubit Pairs

## Overview

Qubits and qubit pairs are essential components in quantum processing units (QPUs), implemented as subclasses of `QuantumComponent`.

## Quantum Components

The `QuantumComponent` class is the base class for qubits and qubit pairs, providing:

- A unique identifier via the `id` property
- A collection of macros defining operations
- An abstract `name` property that derived classes must implement
- A standardized method to apply operations through the `apply()` method

## Qubits

The `Qubit` class models a physical qubit on the QPU, encapsulating:

- Qubit-specific attributes (e.g., frequency)
- Quantum control channels (drive, flux, readout)
- Single-qubit gate operations
- Hardware-specific logic and calibration data

The `Qubit` class is typically subclassed to add channels and other qubit-specific information as properties. Here's an example using a `Transmon` class:

```python
from quam.components import BasicQuam, Qubit, IQChannel, SingleChannel
from quam.core import quam_dataclass

@quam_dataclass
class Transmon(Qubit):
    drive: IQChannel
    flux: SingleChannel

machine = BasicQuam()

q1 = machine.qubits["q1"] = Transmon(
    drive=IQChannel(
        opx_output_I=("con1", 1, 1),
        opx_output_Q=("con1", 1, 2),
        frequency_converter_up=None  # Frequency converter not needed for this example
    ),
    flux=SingleChannel(opx_output=("con1", 1, 3)),
)
```

### Key Features

```python
# Accessing channels
channels = q1.channels  # Returns a dictionary of all channels

# Finding pulses
pulse = q1.get_pulse("pi")  # Retrieves the pulse named "pi" from any channel

# Aligning operations
q1.align()  # Synchronizes all channels of q1
q1.align(q2)  # Synchronizes all channels of q1 and q2
```

## Qubit Pairs

The `QubitPair` class models the interaction between two qubits, managing:

- Two-qubit gate operations
- Coupling elements (e.g., tunable couplers)
  - These can be addd by creating a subclass of `QubitPair` and adding the coupling elements as properties
- Interaction-specific properties and calibrations
- Hardware topology constraints

We create a `QubitPair` using previously defined qubits:

```python
machine.qubit_pairs["q1@q2"] = QubitPair(
    qubit_control=q1.get_reference(),  # = "#/qubits/q1"
    qubit_target=q2.get_reference()  # = "#/qubits/q2"
)
```

The `get_reference()` method ensures each QUAM component has a single parent, which for qubits is the `machine.qubits` dictionary.

### Key Features

Once the qubit pair is added to the root-level [QuamRoot.qubit_pairs][quam.core.quam_classes.QuamRoot.qubit_pairs] dictionary, it can be accessed using the `@` operator:

```python
# Access qubit pair using @ operator
q1 @ q2  # Returns the qubit pair

# Automatic naming
pair = machine.qubit_pairs["q1@q2"]
pair.name  # Returns "q1@q2"

# Applying two-qubit operations
pair.apply("cz_gate")  # Applies the CZ gate macro
```

## Macros and Operations

Both qubits and qubit pairs can contain macros, which serve as high-level interfaces to quantum operations. These macros:

- Define the implementation of quantum gates
- Can be registered in two ways:
  - As instances of a `QuamMacro` subclass, added to `QuantumComponent.macros`
  - As class methods, using the `@QuantumComponent.register_macro` decorator
- Are accessible through the `apply()` method or directly as methods
- Provide a bridge between pulse-level operations and gate-level operations

For detailed information about macros and gate-level operations, see [Gate-Level Operations Documentation](../features/gate-level-operations.md)
