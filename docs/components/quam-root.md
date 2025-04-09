# QUAM Root

The Quantum Abstract Machine (QUAM) utilizes a hierarchical data structure in which each QUAM component can contain nested child components. This architecture is centered around the root QUAM object, which acts as the top-level component and, uniquely, does not have a parent.

## Overview

The root QUAM object is structured as a subclass of [QuamRoot][quam.core.quam_classes.QuamRoot] module. For straightforward implementations, such as those described in the [Migrating to QUAM](/migrating-to-quam) section, the [BasicQUAM][quam.components.basic_quam.BasicQUAM] class typically suffices:

```python
from quam.components import BasicQuam

machine = BasicQuam()
machine.channels["qubit_xy"] = IQChannel(opx_output_I=("con1", 1), opx_output_Q=("con1", 2), ...)
```

## Customizing the Root Object

For more complex setups requiring custom components, you can extend the QUAM root by subclassing and adding your specific components as attributes. This approach allows the QUAM root to be flexible and adaptable to various quantum machine configurations.

### Example of a Custom QUAM Class

```python title="custom_components/quam.py"
from typing import Dict
from quam.core import QuamRoot, quam_dataclass
from quam.components import Octave
from custom_components.qubit import Qubit

@quam_dataclass
class Quam(QuamRoot):
    qubits: Dict[str, Qubit]
    octaves: Dict[str, Octave]
```

You can then instantiate your customized QUAM object, adding components as required for your specific quantum machine setup:

```python
from quam.components import Octave
from custom_components import Quam, Qubit

machine = Quam(
    qubits={"qubit1": Qubit(...), "qubit2": Qubit(...)},
    octaves={"octave1": Octave(...), "octave2": Octave(...)}
)
```

This structured approach ensures that all components of the quantum machine are integrated seamlessly, maintaining a clear and manageable codebase.
