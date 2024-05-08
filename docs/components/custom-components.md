# Custom QuAM Components

To create custom QuAM components, their classes should be defined in a Python module that can be accessed from Python.
The reason for this is that otherwise QuAM cannot load QuAM from a JSON file as it cannot determine where the classes are defined.
If you already have a Python module that you use for your own QUA code, it is recommended to add QuAM components to that module.
If you don't already have such a module, please follow the guide below.

## Creating a Custom Python Module
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

## Creating a Custom QuAM Component
Once a designated Python module has been chosen / created, it can be populated with a custom component.
We will assume that the newly-created Python module `my_quam` is used.
In this example, we will make a basic QuAM component representing a DC gate, with two properties: `name` and `dc_voltage`:

```python title="my_quam/components/gates.py"
from typing import Union
from quam.core import QuamComponent, quam_dataclass

@quam_dataclass
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

- Each QuamComponent inherits from [QuamComponent][quam.core.quam_classes.QuamComponent].
- QuAM components are decorated with `@quam_dataclass`, which is a variant of the Python [@dataclass](https://docs.python.org/3/library/dataclasses.html).

/// details | Reason for `@quam_dataclass` instead of `@dataclass`
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
However, to ensure QuAM is compatible with Python 3.8 and above, we introduced `@quam_dataclass` which fixes this problem:

```python
@quam_dataclass
class Child(Parent):
    required_attr: int
```

An additional benefit is that `kw_only=True` is automatically passed along.  
From Python 3.10 onwards, `@quam_dataclass` is equivalent to `@dataclass(kw_only=True, eq=False)`
///

## QuAM Component Subclassing
QuAM components can also be subclassed to add functionalities to the parent class.
For example, we now want to combine a DC and AC gate together, where the AC part corresponds to an OPX channel.
To do this, we create a class called `AcDcGate` that inherits from both `DcGate` and [SingleChannel][quam.components.channels.SingleChannel]:

```python
from quam.components import SingleChannel


@quam_dataclass
class AcDcGate(DcGate, SingleChannel):
    pass
```

It can be instantiated using
```python
ac_dc_gate = AcDcGate(id="plunger_gate", dc_voltage=0.43, opx_output=("con1", 1))
```

Notice that the keyword argument `opx_output` now also needs to be passed. This is because it's a required argument for [SingleChannel][quam.components.channels.SingleChannel].
