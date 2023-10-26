# Component referencing

## QuAM tree-structure
QuAM follows a tree structure, meaning that each QuAM component can have a parent component and it can have children.

The top-level object is always an instance of QuAMRoot, e.g.
```python
from dataclasses import dataclass
from quam.core import QuamRoot
from quam.components import *

@dataclass
class QuAM(QuamRoot):
    qubit: superconducting_qubits.Transmon = None

machine = QuAM()
```

Next, we can add a qubit as a component:
```python
qubit = superconducting_qubits.Transmon(xy=IQChannel())
machine.qubit = qubit
assert qubit.parent == machine
```

However, situations often arise where a component needs access to another part of QuAM that is not directly one of its children. To accomodate this, we introduce the concept of references.

```
@dataclass
class Component(QuamComponent):
    

component = Component()
component.a = 42
component.b = "#./a
print(component.b)
```
