# QuAM demonstration

In this demonstration we will create a basic superconducting setup using standard components. 
Note that QuAM is not specific to superconducting setups but is meant to serve any quantum platform.

The standard QuAM components can be imported using

```python
from quam.components import *
```

Since we're starting from scratch, we will have to instantiate all QuAM components. This has to be done once, after which we will generally save and load QuAM from a file.
To begin, we create the top-level QuAM object, which inherits from [quam.core.quam_classes.QuamRoot][]. Generally the user is encouraged to create a custom component for this.
```
machine = superconducting_qubits.QuAM()
```

So far, this object is empty, so we'll populate it with objects. Code editors with Python language support (e.g., VS Code, PyCharm) are very useful here because they explain what attributes each class has, what the type should be, and docstrings. This makes it a breeze to create a QuAM from scratch.

In this case, we will create two Transmon objects and fill them with contents:

```python
num_qubits = 2
for idx in range(num_qubits):
    # Create qubit components
    transmon = superconducting_qubits.Transmon(
        id=idx,
        xy=IQChannel(
            local_oscillator=LocalOscillator(power=10, frequency=6e9),
            mixer=Mixer(),
            output_port_I=("con1", 3 * idx + 3),
            output_port_Q=("con1", 3 * idx + 4),
        ),
        z=SingleChannel(output_port=("con1", 3 * idx + 5)),
    )
    machine.qubits.append(transmon)

    # Create resonator components
    resonator = InOutIQChannel(
        input_port_I=("con1", 1),
        input_port_Q=("con1", 2),
        output_port_I=("con1", 1),
        output_port_Q=("con1", 2),
        id=idx, 
        local_oscillator=LocalOscillator(power=10, frequency=6e9),
        mixer=Mixer()
    )
    machine.resonators.append(resonator)
```
This example demonstrates that QuAM follows a tree structure: each component can have a parent and it can have children as attributes.


## Saving and loading QuAM

Now that we have defined our QuAM structure, we can save its contents to a JSON file:

```python
machine.save("state.json")
```

```json | state.json

```