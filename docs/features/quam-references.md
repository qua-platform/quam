# Referencing Between Components

## QuAM Tree Structure
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
qubit = superconducting_qubits.Transmon(xy=IQChannel(opx_output_I=("con1", 1), opx_output_Q=("con1", 2"))
machine.qubit = qubit
assert qubit.parent == machine
```

One of the rules in QuAM is that a component can only have one parent. This is enforced by the `parent` attribute, which is set when a component is added to another component.
As a result, the following raises an error:

```python
channel = IQChannel(opx_output_I=("con1", 1), opx_output_Q=("con1", 2")
qubit1 = superconducting_qubits.Transmon(xy=channel)
qubit2 = superconducting_qubits.Transmon(xy=channel)  # Raises ValueError
``` 
additionally, situations often arise where a component needs access to another part of QuAM that is not directly one of its children. 
To accomodate both of these situations, we introduce the concept of references.

## QuAM References
A reference in QuAM is a way for a component's attribute to be a reference to another part of QuAM. An example is shown here

```python
@quam_dataclass
class Component(QuamComponent):
    a: int
    b: int
    
component = Component(a=42, b="#./a")
print(component.b)  # Prints 42
```
As can be seen, the QuAM component attribute `component.b` was set to a reference, i.e. a string starting with `"#"`. This reference indicates that when the component is retrieved, e.g. through the `print()` statement, it should instead return the value of its reference.

QuAM references follow the JSON reference syntax (For a description see [https://json-spec.readthedocs.io/reference.html](https://json-spec.readthedocs.io/reference.html)), but further allow for relative references, i.e. references w.r.t the current QuAM component. We will next describe the three types of references.

### Absolute References
Absolute references always start with `"#/"`, e.g. `"#/absolute/path/to/value`.
They are references from the top-level QuAM object which inherits from `QuamRoot`
For example:
```python
machine = QuAM()
machine.frequency = 6e9
machine.qubit = Transmon(frequency="#/frequency")
print(machine.qubit.frequency)  # Prints 6e9
```

### Relative References
Relative references start with `"#./"`, e.g. `"#./relative/path/to/value`  
These are references with respect to the current QuAM component.
An example was given above, and is reiterated here:

```python
@quam_dataclass
class Component(QuamComponent):
    a: int
    b: int
    
component = Component(a=42, b="#./a")
print(component.b)  # Prints 42
```

### Relative Parent References
Relative parent references start with `"#../"`, e.g. `"#../relative/path/from/parent/to/value`  
These are references with respect to the parent of the current QuAM component.

To illustrate relative parent references, we modify `Component` to allow for a subcomponent:

```python
@quam_dataclass
class Component(QuamComponent):
    sub_component: "Component" = None
    a: int = None
    b: int = None

component = Component(a=42)
component.subcomponent = Component(a="#../a")
print(component.subcomponent.a)  # Prints 42
```

As can be seen in this example, `component.subcomponent.a = "#../a"` is a relative parent reference, which means that `component.subcomponent.a` should be the same as `component.a`.

Parent references can also be stacked, e.g. `"#../../a"` would be a reference to the grandparent of the current component.


## Additional Notes on References

### Directly Overwriting References is not Allowed
Since QuAM references behave like regular attributes, the user might accidentally overwrite a reference without realizing it. To prohibit this, it is not possible to directly overwrite a reference:

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