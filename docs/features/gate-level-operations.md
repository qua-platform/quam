# Gate-Level Operations

In this guide, we introduce how to build circuit-level QUA programs by focusing on three core concepts:

1. Defining qubits (or qubit pairs)
2. Organizing them within a stateful container (the QUAM)
3. Transforming pulse-level operations into gate-level operations.

By the end of this tutorial, you will be able to construct a simple program of the form:

```python
with program() as prog:
    X(q1)              # Single-qubit gate
    clifford(q1, 4)    # Clifford gate from a predefined set
    qubit_state = measure(q1)
```

This short snippet will apply specific gate operations to qubit q1 and then measure its state.

Below is the outline of what we'll cover:

- Defining a custom Transmon qubit class (inheriting from Qubit)
- Creating a stateful QUAM container to hold multiple qubits or qubit pairs
- Registering a qubit pulse macro (e.g., x180) and using it as a gate
- Building custom macros for measurement and more complex gates (Cliffords)

The goal is to clearly demonstrate the flow from hardware-level pulse definitions all the way to abstract, gate-level instructions in a QUA program.

## Defining a Qubit-Level Component

We'll begin by importing all the modules we need. Then, we'll define a Transmon class that inherits from Qubit.
In this example, a Transmon has an XY channel and an optional resonator channel for readout.

Inheriting from Qubit allows us to attach hardware-specific parameters (like channels) and any additional properties
relevant to our hardware setup.

```python
from typing import Dict, Optional
import numpy as np
from dataclasses import field

from quam.components.ports import FEMPortsContainer
from quam.core import QuamRoot, quam_dataclass
from quam.components.quantum_components import Qubit, QubitPair
from quam.components import MWChannel, InOutMWChannel, pulses

@quam_dataclass
class Transmon(Qubit):
    xy: MWChannel
    resonator: Optional[InOutMWChannel] = None

@quam_dataclass
class Quam(QuamRoot):
    ports: FEMPortsContainer
    qubits: Dict[str, Qubit] = field(default_factory=dict)
    qubit_pairs: Dict[str, QubitPair] = field(default_factory=dict)
```

## Instantiate QUAM

QUAM is our top-level container for organizing ports, qubits, and qubit pairs. We start by creating a Quam instance
that includes a FEMPortsContainer, which helps route signals to and from the hardware.
Then we add two Transmon qubits, "q1" and "q2," referencing their microwave (MW) channels.
These channels are used for generating pulses that interact with the qubits.

```python
machine = Quam(ports=FEMPortsContainer())

## Add qubits
# Here we create the MW output and input ports for q1.
q1_xy_port = machine.ports.get_mw_output("con1", 1, 1, create=True)
q1_resonator_out_port = machine.ports.get_mw_output("con1", 1, 2, create=True)
q1_resonator_in_port = machine.ports.get_mw_input("con1", 1, 2, create=True)

# Next, we instantiate q1 and specify its XY and resonator channels.
q1 = machine.qubits["q1"] = Transmon(
    id="q1",
    xy=MWChannel(intermediate_frequency=100e6, opx_output=q1_xy_port.get_reference()),
    resonator=InOutMWChannel(
        intermediate_frequency=100e6,
        opx_output=q1_resonator_out_port.get_reference(),
        opx_input=q1_resonator_in_port.get_reference(),
    ),
)

# We create another qubit, q2. Here, the resonator channel is omitted for brevity.
q2_xy_mw_output = machine.ports.get_mw_output("con1", 1, 2, create=True)
q2 = machine.qubits["q2"] = Transmon(
    id="q2",
    xy=MWChannel(
        intermediate_frequency=100e6, opx_output=q2_xy_mw_output.get_reference()
    ),
)
```

We can view a quick summary of a qubit's configuration:

```python
q1.print_summary()
```

/// details | `q1.print_summary()` output

```
q1: Transmon
  id: "q1"
  macros: QuamDict Empty
  xy: MWChannel
    operations: QuamDict Empty
    id: None
    digital_outputs: QuamDict Empty
    sticky: None
    intermediate_frequency: 100000000.0
    thread: None
    core: None
    LO_frequency: "#./upconverter_frequency"
    RF_frequency: "#./inferred_RF_frequency"
    opx_output: "#/ports/mw_outputs/con1/1/1"
    upconverter: 1
  resonator: InOutMWChannel
    operations: QuamDict Empty
    id: None
    digital_outputs: QuamDict Empty
    sticky: None
    intermediate_frequency: 100000000.0
    thread: None
    core: None
    opx_input: "#/ports/mw_inputs/con1/1/2"
    time_of_flight: 140
    smearing: 0
    LO_frequency: "#./upconverter_frequency"
    RF_frequency: "#./inferred_RF_frequency"
    opx_output: "#/ports/mw_outputs/con1/1/2"
    upconverter: 1
```

///

## Qubit pairs

Qubit pairs provide an abstraction for interactions between two qubits.
For example, you might need a specific gate that involves both a control qubit and a target qubit.
Here, we create a pair named "q1@q2" which references q1 as control and q2 as target.

```python
machine.qubit_pairs["q1@q2"] = QubitPair(
    qubit_control=q1.get_reference(), qubit_target=q2.get_reference()
)
```

You can then access this pair using:

```python
q1 @ q2
```

/// details | `q1 @ q2` output

```
QubitPair(id='q1@q2', macros={}, qubit_control=Transmon(id='q1', macros={}, xy=MWChannel(operations={}, id=None, digital_outputs={}, sticky=None, intermediate_frequency=100000000.0, thread=None, core=None, LO_frequency=5000000000.0, RF_frequency=5100000000.0, opx_output=MWFEMAnalogOutputPort(controller_id='con1', fem_id=1, port_id=1, band=1, upconverter_frequency=5000000000.0, upconverters=None, delay=0, shareable=False, sampling_rate=1000000000.0, full_scale_power_dbm=-11), upconverter=1), resonator=InOutMWChannel(operations={}, id=None, digital_outputs={}, sticky=None, intermediate_frequency=100000000.0, thread=None, core=None, opx_input=MWFEMAnalogInputPort(controller_id='con1', fem_id=1, port_id=2, band=1, downconverter_frequency=5000000000.0, gain_db=None, sampling_rate=1000000000.0, shareable=False), time_of_flight=140, smearing=0, LO_frequency=5000000000.0, RF_frequency=5100000000.0, opx_output=MWFEMAnalogOutputPort(controller_id='con1', fem_id=1, port_id=2, band=1, upconverter_frequency=5000000000.0, upconverters=None, delay=0, shareable=False, sampling_rate=1000000000.0, full_scale_power_dbm=-11), upconverter=1)), qubit_target=Transmon(id='q2', macros={}, xy=MWChannel(operations={}, id=None, digital_outputs={}, sticky=None, intermediate_frequency=100000000.0, thread=None, core=None, LO_frequency=5000000000.0, RF_frequency=5100000000.0, opx_output=MWFEMAnalogOutputPort(controller_id='con1', fem_id=1, port_id=2, band=1, upconverter_frequency=5000000000.0, upconverters=None, delay=0, shareable=False, sampling_rate=1000000000.0, full_scale_power_dbm=-11), upconverter=1), resonator=None))
```

///

A qubit pair can also be subclassed (similar to how Transmon subclasses Qubit)
if you need extra functionality (e.g., controlling tunable couplers).

## Transforming a Pulse into a Qubit Gate

In QUAM, a common pattern is to define a pulse (e.g., a square pulse) and then wrap it in a macro class.
This macro can be registered as a gate-level operation, allowing us to write high-level QUA code.

For example, below we define an "x180" pulse (a typical pi rotation around the X axis)
and then create a "PulseMacro". This macro is stored in "q1.macros["X"]" so we can call it as a gate.

```python
from quam.components.macro import PulseMacro

# Define the actual pulse — a simple square envelope with amplitude and duration.
q1.xy.operations["x180"] = pulses.SquarePulse(amplitude=0.2, length=100)

# Wrap the pulse in a macro so it can be invoked as a logical gate.
q1.macros["X"] = PulseMacro(pulse=q1.xy.operations["x180"].get_reference())

# Now we can use this macro in a QUA program:
from qm import generate_qua_script, qua

with qua.program() as prog:
    # Apply the X gate to q1. This calls the macro we just defined.
    q1.apply("X")

# Print out the generated QUA code to see how it expands.
print(generate_qua_script(prog))
```

/// details | Pulse macro output

```python
# Single QUA script generated at 2025-03-31 19:28:57.397848
# QUA library version: 1.2.2a4

from qm import CompilerOptionArguments
from qm.qua import *

with program() as prog:
    play("x180", "q1.xy")


config = None

loaded_config = None
```

///

### Creating operations

To make a macro like "X" accessible as a gate-level operation in QUA,
we use an OperationsRegistry. The registry maps gate names (like X) to the correct macro for each qubit.

```python
from quam.core.operation import OperationsRegistry

operations_registry = OperationsRegistry()

@operations_registry.register_operation
# The function name below becomes the gate-level call (e.g., X(q1)).
# Note that internally, it will trigger the macro we assigned to "q1.macros["X"]".
def X(qubit: Qubit, **kwargs):
    # Implementation is resolved by the macros attached to the qubit.
    pass
```

Now calling X(q1) in QUA code triggers the macro q1.macros["X"].

```python
with qua.program() as prog:
    # This uses the registry to look up the correct macro.
    X(q1)

print(generate_qua_script(prog))
```

/// details | Operation program output

```python
from quam.components.macro import PulseMacro

# Define the actual pulse — a simple square envelope with amplitude and duration.
q1.xy.operations["x180"] = pulses.SquarePulse(amplitude=0.2, length=100)

# Wrap the pulse in a macro so it can be invoked as a logical gate.
q1.macros["X"] = PulseMacro(pulse=q1.xy.operations["x180"].get_reference())

# Now we can use this macro in a QUA program:
from qm import generate_qua_script, qua

with qua.program() as prog:
    # Apply the X gate to q1. This calls the macro we just defined.
    q1.apply("X")

# Print out the generated QUA code to see how it expands.
print(generate_qua_script(prog))
```

///

## Creating custom macros

Often, a gate corresponds to a single pulse, and "PulseMacro" is enough. But sometimes, a gate may require
multiple pulses or more complex logic. In that case, we can define a custom macro by subclassing QubitMacro
(or QubitPairMacro if it involves two qubits).

Below, we create two macros as examples: a "measure" macro and a "clifford" macro.
These illustrate how to embed logic into your macros and integrate them with the QUAM.

### Measure macro

For the measure macro, we define a readout pulse on q1's resonator channel. The macro itself, when called,
plays that pulse, reads I/Q data, and assigns a boolean state based on a threshold.

```python
q1.resonator.operations["readout"] = pulses.SquareReadoutPulse(
    length=1000, amplitude=0.1, threshold=0.215
)
```

```python
from quam.components.macro import QubitMacro
from quam.utils.qua_types import QuaVariableBool

@quam_dataclass
class MeasureMacro(QubitMacro):
    threshold: float

    def apply(self, **kwargs) -> QuaVariableBool:
        # The macro reads I/Q data from the resonator channel.
        I, Q = self.qubit.resonator.measure("readout")
        # We declare a QUA variable to store the boolean result of thresholding the I value.
        qubit_state = qua.declare(bool)
        qua.assign(qubit_state, I > self.threshold)
        return qubit_state
```

We attach an instance of this MeasureMacro to our qubit q1.

```python
q1.macros["measure"] = MeasureMacro(threshold=0.215)
```

Now we can perform the "measure" operation within a QUA program:

```python
with qua.program() as prog:
    qubit_state = q1.apply("measure")  # returns a boolean variable

print(generate_qua_script(prog))
```

Similar to the X gate, we can register a generic measure() operation:

```python
@operations_registry.register_operation
def measure(qubit: Qubit, **kwargs) -> QuaVariableBool:
    pass
```

This lets us call measure(q1) in a gate-like manner:

```python
with qua.program() as prog:
    qubit_state = measure(q1)

print(generate_qua_script(prog))
```

/// details | Measure macro output

```python
# Single QUA script generated at 2025-03-31 19:28:57.445853
# QUA library version: 1.2.2a4

from qm import CompilerOptionArguments
from qm.qua import *

with program() as prog:
    v1 = declare(fixed, )
    v2 = declare(fixed, )
    v3 = declare(bool, )
    measure("readout", "q1.resonator", dual_demod.full("iw1", "iw2", v1), dual_demod.full("iw3", "iw1", v2))
    assign(v3, (v1>0.215))


config = None

loaded_config = None
```

///

### Clifford macro

Next, we define a single-qubit "CliffordMacro". For illustration, we will define a few pulses
that correspond to some of the first five Clifford gates.

```python
# Define additional pulses for x90, x180, y90, y180, etc.
q1.xy.operations["x90"] = pulses.SquarePulse(amplitude=0.1, length=100, axis_angle=0)
q1.xy.operations["x180"] = pulses.SquarePulse(amplitude=0.2, length=100, axis_angle=0)
q1.xy.operations["y90"] = pulses.SquarePulse(amplitude=0.1, length=100, axis_angle=np.pi / 2)
q1.xy.operations["y180"] = pulses.SquarePulse(amplitude=0.2, length=100, axis_angle=np.pi / 2)
```

```python
@quam_dataclass
class CliffordMacro(QubitMacro):
    def apply(self, clifford_idx: int, **kwargs):
        # We use a QUA switch_ statement to choose which pulses to play in real time.
        with qua.switch_(clifford_idx, unsafe=True):
            with qua.case_(0):
                # Identity operation: do nothing except wait to preserve timing.
                wait_duration = self.qubit.xy.operations["x180"].length // 4
                self.qubit.xy.wait(wait_duration)
            with qua.case_(1):
                self.qubit.xy.play("x180")
            with qua.case_(2):
                self.qubit.xy.play("y180")
            with qua.case_(3):
                self.qubit.xy.play("y180")
                self.qubit.xy.play("x180")
            with qua.case_(4):
                # This is a composite gate (x90 followed by y90)
                self.qubit.xy.play("x90")
                self.qubit.xy.play("y90")
            # You can continue defining more Clifford cases here...

# Attach the macro to q1
q1.macros["clifford"] = CliffordMacro()

# We can now call this macro using q1.apply("clifford", clifford_idx):
with qua.program() as prog:
    clifford_idx = qua.declare(int, 0)
    q1.apply("clifford", clifford_idx)


# As before, we register a qubit-generic function:
@operations_registry.register_operation
def clifford(qubit: Qubit, clifford_idx: int, **kwargs):
    pass

# Now we can call clifford(q1, clifford_idx) in our QUA program:
with qua.program() as prog:
    clifford_idx = qua.declare(int, 0)
    clifford(q1, clifford_idx)

print(generate_qua_script(prog))
```

/// details | Clifford output

```python
# Single QUA script generated at 2025-03-31 19:28:57.522055
# QUA library version: 1.2.2a4

from qm import CompilerOptionArguments
from qm.qua import *

with program() as prog:
    v1 = declare(int, value=0)
    with if_((v1==0), unsafe=True):
        wait(25, "q1.xy")
    with elif_((v1==1)):
        play("x180", "q1.xy")
    with elif_((v1==2)):
        play("y180", "q1.xy")
    with elif_((v1==3)):
        play("y180", "q1.xy")
        play("x180", "q1.xy")
    with elif_((v1==4)):
        play("x90", "q1.xy")
        play("y90", "q1.xy")


config = None

loaded_config = None
```
