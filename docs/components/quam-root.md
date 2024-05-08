# QuAM Root

The Quantum Abstract Machine (QuAM) utilizes a hierarchical data structure in which each QuAM component can contain nested child components. This architecture is centered around the root QuAM object, which acts as the top-level component and, uniquely, does not have a parent.

## Overview

The root QuAM object is structured as a subclass of [QuamRoot][quam.core.quam_classes.QuamRoot] module. For straightforward implementations, such as those described in the [Migrating to QuAM](/migrating-to-quam) section, the [BasicQuAM][quam.components.basic_quam.BasicQuAM] class typically suffices:

```python
from quam.components import BasicQuAM

machine = BasicQuAM()
machine.channels["qubit_xy"] = IQChannel(opx_output_I=("con1", 1), opx_output_Q=("con1", 2), ...)
```

## Customizing the Root Object

For more complex setups requiring custom components, you can extend the QuAM root by subclassing and adding your specific components as attributes. This approach allows the QuAM root to be flexible and adaptable to various quantum machine configurations.

### Example of a Custom QuAM Class

```python title="custom_components/quam.py"
from typing import Dict
from quam.core import QuamRoot, quam_dataclass
from quam.components import Octave
from custom_components.qubit import Qubit

@quam_dataclass
class QuAM(QuamRoot):
    qubits: Dict[str, Qubit]
    octaves: Dict[str, Octave]
```

You can then instantiate your customized QuAM object, adding components as required for your specific quantum machine setup:

```python
from quam.components import Octave
from custom_components import QuAM, Qubit

machine = QuAM(
    qubits={"qubit1": Qubit(...), "qubit2": Qubit(...)},
    octaves={"octave1": Octave(...), "octave2": Octave(...)}
)
```

This structured approach ensures that all components of the quantum machine are integrated seamlessly, maintaining a clear and manageable codebase.
