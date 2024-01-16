# Component referencing

## QuAM tree-structure
QuAM follows a tree structure, meaning that each QuAM component can have a parent component and it can have children.

The top-level object is always an instance of QuAMRoot, e.g.
```python
from dataclasses import dataclass
from quam.core import QuamRoot, quam_dataclass
from quam.components import *

@quam_dataclass
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

## QuAM references
A reference in QuAM is a way for a component's attribute to be a reference to another part of QuAM. An example is shown here

```python
@quam_dataclass
class Component(QuamComponent):
    

component = Component()
component.a = 42
component.b = "#./a"
print(component.b)  # Prints 42
```
As can be seen, the Quam component attribute `component.b` was set to a reference, i.e. a string starting with `"#"`. This reference indicates that when the component is retrieved, e.g. through the `print()` statement, it should instead return the value of its reference.

Quam references follow the JSON pointer syntax (For a description see https://datatracker.ietf.org/doc/html/rfc6901), but further allow for relative references, i.e. references w.r.t the current Quam component. We will next describe the three types of references.

### Absolute references
Absolute references always start with `"#/"`, e.g. `"#/absolute/path/to/value`.
They are references from the top-level QuAM object which inherits from `QuamRoot`
For example:
```python
machine = QuAM()
machine.frequency = 6e9
machine.qubit = Transmon(frequency="#/frequency")
print(machine.qubit.frequency)  # Prints 6e9
```

### Relative references
Relative references start with `"#./"`, e.g. `"#./relative/path/to/value`  
These are references with respect to the current QuAM component.
An example was given above, and is reiterated here:

```python
@quam_dataclass
class Component(QuamComponent):
    

component = Component()
component.a = 42
component.b = "#./a"
print(component.b)  # Prints 42
```

### Relative parent references
Relative parent references start with `"#../"`, e.g. `"#../relative/path/from/parent/to/value`  
These are references with respect to the parent of the current QuAM component.
Note that the parent
An example was given above, and is reiterated here:

```python
@quam_dataclass
class Component(QuamComponent):
    

component = Component()
component.a = 42
component.b = "#./a"
print(component.b)  # Prints 42
```

## Additional notes on references

### Directly overwriting references is not allowed
Since Quam references behave like regular attributes, the user might accidentally overwrite a reference without realizing it. To prohibit this, it is not possible to directly overwrite a reference:

```python
component = Component()
component.a = 42
component.b = "#./a"

component.b = 43  # Raises ValueError
```

Instead, a reference must first be set to None, after which it can be set to an arbitrary new value (including a new reference):
```python
component.b = "#./a"
component.b = None
component.b = 43  # Does not raise an error
```