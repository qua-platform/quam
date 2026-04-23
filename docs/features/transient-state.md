# Transient State

Transient state lets you make temporary changes to a [QuamRoot][quam.core.quam_classes.QuamRoot] object for runtime use without persisting those changes to disk.

Use it when you need a modified value to be visible to normal QUAM access, config generation, or experiment logic, but want `save()` to keep the original calibrated state.

## Basic Usage

Record temporary writes inside `record_transient()`:

```python
from dataclasses import field

from quam import QuamRoot, quam_dataclass
from quam.core import QuamComponent


@quam_dataclass
class Qubit(QuamComponent):
    frequency: float = 5e9


@quam_dataclass
class TransientMachine(QuamRoot):
    qubit: Qubit = field(default_factory=Qubit)


machine = TransientMachine()

with machine.record_transient():
    machine.qubit.frequency = 5.1e9

print(machine.qubit.frequency)  # 5.1e9
```

The context manager records the original value. It does not roll the value back when the `with` block exits. This allows the temporary value to remain active for later runtime operations:

```python
qua_config = machine.generate_config()
```

## Inspecting Changes

Use `get_transient_changes()` to inspect the active transient records:

```python
changes = machine.get_transient_changes()
print(changes)
```

Each change is described as a dictionary with:

- `path`: the QUAM path of the changed value
- `was`: the original pre-transient value
- `now`: the current transient value

For the example above, the result is:

```python
[
    {
        "path": "#/qubit/frequency",
        "was": 5e9,
        "now": 5.1e9,
    }
]
```

Only the first write to a given attribute, dictionary key, or list is recorded. Later writes update the live value, but the original `was` value remains the value that will be restored.

## Reverting Explicitly

Call `revert_transient()` when you want to discard all active transient changes and return to the recorded original state:

```python
with machine.record_transient():
    machine.qubit.frequency = 5.1e9

machine.revert_transient()

print(machine.qubit.frequency)  # 5e9
print(machine.get_transient_changes())  # []
```

## Dictionaries and Lists

Transient recording also tracks writes through QUAM dictionaries and lists.

Dictionary mutations are recorded per key:

```python
@quam_dataclass
class SettingsMachine(QuamRoot):
    settings: dict = field(default_factory=lambda: {"mode": "idle"})


machine = SettingsMachine()

with machine.record_transient():
    machine.settings["mode"] = "run"
    machine.settings["temporary"] = True

print(machine.get_transient_changes())
```

List mutations are recorded as a snapshot of the whole list:

```python
@quam_dataclass
class SweepMachine(QuamRoot):
    sweep_points: list = field(default_factory=lambda: [1, 2])


machine = SweepMachine()

with machine.record_transient():
    machine.sweep_points.append(3)
    machine.sweep_points[0] = 0

print(machine.get_transient_changes())
# [{"path": "#/sweep_points", "was": [1, 2], "now": [0, 2, 3]}]
```

For added or deleted dictionary keys, `was` or `now` is the `MISSING` sentinel from `quam.core.transient`.

## Saving With Active Transient Changes

When `save()` is called while transient changes are active, QUAM:

1. Emits a `UserWarning` with the number of active transient changes.
2. Reverts the object to the original pre-transient values.
3. Saves those original values to disk.
4. Clears the transient records after a successful save.

```python
from pathlib import Path

machine = TransientMachine()

with machine.record_transient():
    machine.qubit.frequency = 5.1e9

machine.save(Path("state.json"))

print(machine.qubit.frequency)  # 5e9
print(machine.get_transient_changes())  # []
```

This means `save()` is a persistence boundary: active transient changes affect runtime behavior until saving, but the saved JSON contains the original values.

If saving fails after QUAM has reverted the transient values, QUAM restores the transient live state and records before raising the original exception.

## Overwriting a Transient Value Permanently

If a recorded transient value is overwritten outside a `record_transient()` scope, QUAM treats that as a permanent write. It warns and removes the transient record:

```python
with machine.record_transient():
    machine.qubit.frequency = 5.1e9

machine.qubit.frequency = 5.2e9  # warns; this value is now permanent

print(machine.get_transient_changes())  # []
```

After this happens, `revert_transient()` will not restore the old value for that path because the transient record has been removed.

## Limitations

- Nested `record_transient()` scopes are not supported and raise `RuntimeError`.
- Detached components are not recorded into the last instantiated root; only objects attached to the active root are tracked.
- List changes are tracked at list granularity, not per index.
- Transient state is for runtime mutations. Use `skip_save` metadata for fields that should never be serialized, even when they are not transient.
