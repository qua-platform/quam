# Serialization and State Management

QUAM provides powerful serialization capabilities to save and load your quantum machine configurations. This allows you to persist your setup between sessions, version control your configurations, and easily share setups with collaborators.

## Basic Serialization

### Saving a QUAM State

You can save your QUAM configuration to a JSON file using the `save()` method:

```python
from quam import QuamRoot, quam_dataclass

machine = QuamRoot()
# ... configure your machine ...
machine.save("state.json")
```

### Loading a QUAM State

Load a previously saved configuration using the `load()` class method:

```python
machine = QuamRoot.load("state.json")
```

### Converting to Dictionary

Convert a QUAM object to a dictionary representation without saving to disk:

```python
config_dict = machine.to_dict()
```

## Controlling Default Values

By default, QUAM includes all field values (including defaults) in serialized output. You can control this behavior using the `include_defaults` parameter:

```python
# Include default values (default behavior)
machine.save("state.json", include_defaults=True)

# Exclude default values (only save non-default values)
machine.save("state.json", include_defaults=False)
```

## Excluding Fields from Serialization

Sometimes you may want certain fields to be accessible at runtime but not saved to disk. Common use cases include:

- Temporary cached data
- Runtime-only connections (e.g., `qm` or `qmm` objects from QM)
- Computed properties that shouldn't be persisted
- Sensitive information that shouldn't be stored

### Using `skip_save` Metadata

You can exclude specific fields from serialization using the `skip_save` metadata flag:

```python
from dataclasses import field
from quam import quam_dataclass, QuamComponent

@quam_dataclass
class MyComponent(QuamComponent):
    # This field will be saved
    persistent_value: int = 1

    # This field will NOT be saved (skip_save=True)
    runtime_only_value: int = field(default=2, metadata={"skip_save": True})

    # You can also skip complex objects
    cached_data: dict = field(default_factory=dict, metadata={"skip_save": True})
```

**Key behaviors:**

- Fields marked with `skip_save=True` are excluded from both `to_dict()` and `save()` operations
- These fields remain fully accessible at runtime (you can read and write them normally)
- If a field contains a `QuamComponent`, the entire component tree is excluded from serialization

### Example: Quantum Machine Manager

A common use case is excluding the Quantum Machines manager objects from serialization:

```python
from dataclasses import field
from quam import QuamRoot, quam_dataclass

@quam_dataclass
class QuantumMachine(QuamRoot):
    # Configuration that should be saved
    ip_address: str = "127.0.0.1"
    port: int = 9510

    # Runtime objects that should NOT be saved
    qm: object = field(default=None, metadata={"skip_save": True})
    qmm: object = field(default=None, metadata={"skip_save": True})

    def connect(self):
        """Connect to the quantum machine."""
        from qm.QuantumMachinesManager import QuantumMachinesManager
        self.qmm = QuantumMachinesManager(host=self.ip_address, port=self.port)
        self.qm = self.qmm.open_qm(self.generate_config())

# Usage
machine = QuantumMachine()
machine.connect()  # Creates qm and qmm objects

# Save configuration (qm and qmm are automatically excluded)
machine.save("state.json")

# Load configuration (need to reconnect)
machine = QuantumMachine.load("state.json")
machine.connect()  # Re-establish connection
```

### Nested Component Exclusion

When a field containing a `QuamComponent` is marked with `skip_save=True`, the entire component tree under that field is excluded:

```python
@quam_dataclass
class InnerComponent(QuamComponent):
    inner_value: int = 1

@quam_dataclass
class OuterComponent(QuamComponent):
    visible: int = 2
    # This entire component (including inner_value) won't be saved
    hidden: InnerComponent = field(
        default_factory=InnerComponent,
        metadata={"skip_save": True}
    )

obj = OuterComponent()
result = obj.to_dict()
# result only contains: {"visible": 2, "__class__": "...OuterComponent"}
# The entire 'hidden' component and its nested data are excluded
```

### Inheritance and Field Override

Field metadata is preserved through inheritance but can be overridden in child classes:

```python
@quam_dataclass
class Parent(QuamComponent):
    # Hidden in parent
    field: int = field(default=1, metadata={"skip_save": True})

@quam_dataclass
class Child(Parent):
    # Override to make it visible in child
    field: int = 2  # No metadata = will be saved

parent = Parent()
parent.to_dict()  # field excluded

child = Child()
child.to_dict()  # field included
```

## Best Practices

1. **Use `skip_save` for runtime-only data**: Mark fields that contain session-specific or computed data
2. **Keep configurations portable**: Exclude machine-specific or environment-specific data
3. **Document exclusions**: Comment why certain fields are excluded to help future maintainers
4. **Test serialization**: Verify that save/load cycles preserve your configuration correctly
5. **Version your configs**: Keep saved states in version control to track configuration evolution

## Scope and Limitations

- `skip_save` only applies to dataclass fields, not items within `QuamList` or `QuamDict`
- Metadata is class-level (defined at class definition time), not instance-level
- You cannot dynamically change `skip_save` behavior for individual instances
