# Qubits and Qubit Pairs

## Overview
Qubits and qubit pairs are essential components in quantum processing units (QPUs), implemented as subclasses of `QuantumComponent`. 

### Qubits
The `Qubit` class models a physical qubit on the QPU, encapsulating:
- Qubit-specific attributes (e.g., frequency)
- Quantum control channels (drive, flux, readout)
- Single-qubit gate operations
- Hardware-specific logic and calibration data

The `Qubit` class is typically subclassed to add channels and other qubit-specific information as properties. In this example, we define a `Transmon` class, a subclass of `Qubit`, with specific channels:

```python
from quam.components import BasicQuam, Qubit, IQChannel, SingleChannel
from quam.core import quam_dataclass

@quam_dataclass
class Transmon(Qubit):
    drive: IQChannel
    flux: SingleChannel

machine = BasicQuam()
```

We create two qubit instances, `q1` and `q2`, as follows:

```python
q1 = machine.qubits["q1"] = Transmon(
    drive=IQChannel(
        opx_output_I=("con1", 1, 1),
        opx_output_Q=("con1", 1, 2),
        frequency_converter_up=None),
    flux=SingleChannel(opx_output=("con1", 1, 3)),
)

q2 = machine.qubits["q2"] = Transmon(
    drive=IQChannel(
        opx_output_I=("con1", 1, 5),
        opx_output_Q=("con1", 1, 6),
        frequency_converter_up=None),
    flux=SingleChannel(opx_output=("con1", 1, 7)),
)
```

### Qubit Pairs
The `QubitPair` class models the interaction between two qubits, managing:
- Two-qubit gate operations
- Coupling elements (e.g., tunable couplers)
- Interaction-specific properties and calibrations
- Hardware topology constraints

We create a `QubitPair` using the qubits `q1` and `q2`:

```python
machine.qubit_pairs["q1@q2"] = QubitPair(
    qubit_control=q1.get_reference(),  # "#/qubits/q1"
    qubit_target=q2.get_reference()  # "#/qubits/q2"
)
```

The `get_reference()` method is used to obtain a reference to the qubit, ensuring each QuAM component has a single parent, which for qubits is the `machine.qubits` dictionary.

Both components offer interfaces for quantum operations through macros, enabling hardware-agnostic control while maintaining device-specific implementations.

## Quantum Components
The `QuantumComponent` class is the base class for qubits and qubit pairs, providing:
- A unique identifier via the `id` property
- A collection of macros defining operations
- An abstract `name` property that derived classes must implement
- A standardized method to apply operations through the `apply()` method

## Qubits
A `Qubit` represents a single quantum bit, acting as:
- A container for quantum control channels (drive, flux, readout, etc.)
- A collection point for pulse operations on its channels
- An endpoint for single-qubit operations via macros



### Key Features

```python
# Accessing channels
channels = q1.channels  # Returns a dictionary of all channels

# Finding pulses
pulse = q1.get_pulse("pi")  # Retrieves the pulse named "pi" from any channel

# Aligning operations
q1.align(q2)  # Synchronizes all channels of q1 and q2
```

## Qubit Pairs
A `QubitPair` represents the relationship between two qubits, typically used for two-qubit operations. It includes:
- References to both the control and target qubits
- Macros for two-qubit operations
- Automatic naming based on the constituent qubits

### Key Features

Once the qubit pair is added to the root-level [QuamRoot.qubit_pairs][quam.core.quam_classes.QuamRoot.qubit_pairs] dictionary, it can be accessed directly from the qubits using the `@` operator:

```python
q1 @ q2  # Returns the qubit pair
```
```python
# Automatic naming
pair = machine.qubit_pairs["q1@q2"]
pair.name  # Returns "q1@q2"

# Accessing qubits
pair.qubit_control, pair.qubit_target  # Returns the control and target qubits

# Applying two-qubit operations
pair.apply("cz_gate")  # Applies the CZ gate macro
```


## Macros and Operations
Both qubits and qubit pairs can contain macros, which serve as high-level interfaces to quantum operations. These macros:
- Define the implementation of quantum gates
- Can be registered using the `@QuantumComponent.register_macro` decorator
- Are accessible through the `apply()` method or directly as methods
- Provide a bridge between the hardware configuration and gate-level operations

For detailed information about macros and gate-level operations, see:
- [Macros Documentation](./macros.md)
- [Gate-Level Operations Documentation](./operations.md)

This documentation provides a high-level overview of the qubit and qubit pair functionality while referencing the macro and gate-level operations that will be detailed in other documentation pages.