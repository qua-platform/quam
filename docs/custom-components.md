# Custom components

To create custom QuAM components, their classes should be defined in a Python module that can be accessed from Python.
The reason for this is that otherwise QuAM cannot load QuAM from a JSON file as it cannot determine where the classes are defined.
If you already have a Python module that you use for your own QUA code, it is recommended to add QuAM components to that module.
If you don't already have such a module, please follow the guide below.

## Creating a custom Python module
Here we describe how to create a minimal Python module that can be used for your custom QuAM components.
In this example, we will give the top-level folder the name `my-quam` and the Python module will be called `my_quam` (note the underscore instead of dash).
First create the following folder structure
```
my-quam
├── my_quam
│   └── components
│       └── __init__.py
└── pyproject.toml
```
The file `__init__.py` should be empty, and `pyproject.toml` should have the following contents:

/// details | pyproject.toml
```toml
[project]
name = "my-quam"
version = "0.1.0"
description = "User QuAM repository"
authors = [{ name = "Jane Doe", email = "jane.doe@quantum-machines.co" }]
requires-python = ">=3.8"

[build-system]
requires = ["setuptools", "setuptools-scm"]
build-backend = "setuptools.build_meta"


[tool.setuptools]
packages = ["my_quam"]
```
///

Feel free to modify details such as `description` and `authors`.

Finally, to install the package, first make sure you're in the correct environment, then navigate to the top-level folder `my-quam` and run:
```
pip install .
```
The custom QuAM components can then be loaded as
```python
from my_quam.components import *
```
All the custom QuAM components should be placed as Python files in `my-quam/my_quam/components`.

## Creating a custom QuAM component
Once a designated Python module has been chosen / created, it can be populated with a custom component.
We will assume that the newly-created Python module `my_quam` is used.
In this example, we will make a basic QuAM component representing a DC gate, with two properties: `name` and `dc_voltage`:

```python title="my_quam/components/gates.py"
from dataclasses import dataclass
from typing import Union
from quam.core import QuamComponent

@dataclass(kw_only=True, eq=True)
class DcGate(QuamComponent):
    id: Union[int, str]
    dc_voltage: float
```
which can be instantiated as follows:
```python
from my_quam.components.gates import DcGate
dc_gate = DcGate(id="plunger_gate", dc_voltage=0.43)
```

A few notes about the above:

- Each QuamComponent inherits from [quam.core.quam_classes.QuamComponent][].
- A QuAM component should be a [Python dataclass](https://docs.python.org/3/library/dataclasses.html).
- We add the keyword arguments `@dataclass(kw_only=True, eq=True)`. We recommend doing so for every QuAM component, the reason for this is described below.

## QuAM component subclassing
QuAM components can also be subclassed to add functionalities to the parent class.
For example, we now want to combine a DC and AC gate together, where the AC part corresponds to an OPX channel.
To do this, we create a class called `AcDcGate` that inherits from both `DcGate` and [quam.components.channels.SingleChannel][]:

```python
from quam.components import SingleChannel


@dataclass(kw_only=True, eq=True)
class AcDcGate(DcGate, SingleChannel):
```

It can be instantiated using
```python
ac_dc_gate = AcDcGate(id="plunger_gate", dc_voltage=0.43, opx_output=("con1", 1))
```

Notice that the keyword argument `opx_output` now also needs to be passed. This is because it's a required argument for [quam.components.channels.SingleChannel][].

### Limitations when inheriting from a dataclass
Inheriting from a dataclass is not directly possible when the parent class has keyword arguments and the child class does not.
To illustrate this, the following example will raise a `TypeError`:
```python
@dataclass
class Parent:
    optional_attr: int = 42

@dataclass
class Child(Parent):
    required_attr: int
```

In Python 3.10 and up, this can be solved by adding the `kw_only=True` keyword argument:
```python
@dataclass
class Parent:
    optional_attr: int = 42

@dataclass(kw_only=True)
class Child(Parent):
    required_attr: int

child = Child(required_attr=12)  # Note that we now need to explicitly pass keywords
```

The keyword `kw_only` was only introduced in Python 3.10, and so the example above would raise an error in Python <3.10.
To make the code compatible with Python 3.9 and lower, we introduced a patch that allows `kw_only` to be used in Python <3.10.
To enable this patch, the following lines should be added to the top of each file that has QuAM components:
```python
from quam.utils import patch_dataclass
patch_dataclass(__name__)  # Ensure dataclass "kw_only" also works with python < 3.10
```