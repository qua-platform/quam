# Transient State

Transient state lets you make temporary changes to a [QuamRoot][quam.core.quam_classes.QuamRoot] object for runtime use without saving those changes as calibrated state.

This is useful in calibration routines. A routine may need to temporarily change a machine parameter before generating a QUA config or running a program. That temporary value should affect the experiment, but it should not be persisted unless the later analysis decides it is the right calibrated value.

## Motivation

Consider a readout calibration that sweeps readout power. Before generating the QUA config, the calibration may need to raise the readout pulse amplitude to the maximum value used in the sweep. This ensures that the generated config contains a pulse large enough for all amplitude-scale factors used by the program.

That maximum amplitude is not necessarily the value you want to save. It is a temporary runtime value used to run the sweep. After analysis, the calibration may choose a different fitted amplitude as the value to keep.

Transient state separates these two steps:

1. Record and apply temporary values for config generation or execution.
2. Revert those temporary values.
3. Save only the final calibrated values selected by the analysis.

## Complete Example

The following script uses the superconducting-qubits example components from `quam.examples.superconducting_qubits`. It creates a small QUAM, adds readout pulses, temporarily increases the readout amplitudes for config generation, then reverts those temporary values before saving the fitted calibration result.

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from quam.components import pulses
from quam.examples.superconducting_qubits.generate_superconducting_quam import (
    create_quam_superconducting_referenced,
)


machine = create_quam_superconducting_referenced(num_qubits=2)

for qubit in machine.qubits.values():
    qubit.resonator.operations["readout"] = pulses.SquareReadoutPulse(
        length=1000,
        amplitude=0.05,
    )

max_readout_amplitude = 0.2

with machine.record_transient():
    for qubit in machine.qubits.values():
        qubit.resonator.operations["readout"].amplitude = max_readout_amplitude

config = machine.generate_config()
assert config["waveforms"]["IQ0.readout.wf.I"]["sample"] == max_readout_amplitude

print(machine.get_transient_changes())

machine.revert_transient()
assert machine.qubits["q0"].resonator.operations["readout"].amplitude == 0.05

fitted_amplitudes = {
    "q0": 0.08,
    "q1": 0.07,
}

for qubit_name, amplitude in fitted_amplitudes.items():
    machine.qubits[qubit_name].resonator.operations["readout"].amplitude = amplitude

with TemporaryDirectory() as tmpdir:
    state_path = Path(tmpdir) / "state.json"
    machine.save(state_path)
```

This is the main transient-state pattern:

- Use transient values to run the experiment.
- Revert the transient values after they are no longer needed.
- Use normal assignments for the analyzed calibration result.
- Save only the values you intend to keep.

## Recording Temporary Values

The transient recording scope is the part of the script where temporary values are assigned:

```python
with machine.record_transient():
    for qubit in machine.qubits.values():
        qubit.resonator.operations["readout"].amplitude = max_readout_amplitude
```

`record_transient()` records the original values before the writes happen. It does not revert the values when the `with` block exits. The temporary values remain live on the machine:

```python
print(machine.qubits["q0"].resonator.operations["readout"].amplitude)
# 0.2
```

This is the key behavior: the temporary values are available to normal QUAM access and config generation.

## Generate a Config With Temporary Values

After recording the temporary changes, generate the config as usual:

```python
config = machine.generate_config()
```

The generated config sees the temporary readout amplitudes because they are still live on the QUAM object:

```python
print(config["waveforms"]["IQ0.readout.wf.I"]["sample"])
# 0.2
```

This lets the calibration run with the values needed for the experiment without making those values permanent.

## Inspect and Revert

Use `get_transient_changes()` to see what is currently recorded:

```python
changes = machine.get_transient_changes()
print(changes)
```

The output contains the QUAM path, the original value, and the current temporary value:

```python
[
    {
        "path": "#/qubits/q0/resonator/operations/readout/amplitude",
        "was": 0.05,
        "now": 0.2,
    },
    {
        "path": "#/qubits/q1/resonator/operations/readout/amplitude",
        "was": 0.05,
        "now": 0.2,
    },
]
```

When the temporary values are no longer needed, revert them:

```python
machine.revert_transient()

print(machine.qubits["q0"].resonator.operations["readout"].amplitude)
# 0.05
print(machine.get_transient_changes())
# []
```

The machine is now back to the state it had before the temporary calibration changes.

## Save Only the Calibration Result

After the experiment and analysis, apply the values you actually want to persist using normal assignments:

```python
machine.revert_transient()

fitted_amplitudes = {
    "q0": 0.08,
    "q1": 0.07,
}

for qubit_name, amplitude in fitted_amplitudes.items():
    machine.qubits[qubit_name].resonator.operations["readout"].amplitude = amplitude

machine.save("state.json")
```

The distinction is important:

- Transient values are for running the experiment.
- Normal assignments are for calibrated values you intend to keep.

This pattern prevents temporary sweep setup from being accidentally saved as the machine's calibrated state.

## Saving With Active Transient Changes

`save()` also has a safety behavior. If transient changes are still active when you save, QUAM:

1. Emits a `UserWarning` with the number of active transient changes.
2. Reverts the object to the original pre-transient values.
3. Saves those original values to disk.
4. Clears the transient records after a successful save.

```python
with machine.record_transient():
    machine.qubits["q0"].resonator.operations["readout"].amplitude = 0.2

machine.save("state.json")
```

In this case, the saved state contains the original amplitude, not `0.2`.

This behavior is a guardrail. In calibration code, it is usually clearer to call `revert_transient()` explicitly before applying and saving the final fitted values.

If saving fails after QUAM has reverted the transient values, QUAM restores the transient live state and records before raising the original exception.

## Additional Details

### First Write Is Recorded

Only the first write to a given attribute, dictionary key, or list is recorded. Later writes update the live value, but the original `was` value remains the value that will be restored:

```python
with machine.record_transient():
    readout = machine.qubits["q0"].resonator.operations["readout"]
    readout.amplitude = 0.1
    readout.amplitude = 0.2

print(machine.get_transient_changes())
# [{"path": ".../amplitude", "was": 0.05, "now": 0.2}]
```

### Dictionaries and Lists

Transient recording also tracks writes through QUAM dictionaries and lists.

Dictionary mutations are recorded per key:

```python
with machine.record_transient():
    machine.wiring["temporary_mode"] = "power_sweep"
```

For added or deleted dictionary keys, `was` or `now` is the `MISSING` sentinel from `quam.core.transient`.

List mutations are recorded as a snapshot of the whole list:

```python
machine.wiring["active_qubits"] = ["q0", "q1"]

with machine.record_transient():
    machine.wiring["active_qubits"].append("q2")

print(machine.get_transient_changes())
# [{"path": "#/wiring/active_qubits", "was": ["q0", "q1"], "now": ["q0", "q1", "q2"]}]
```

List changes are tracked at list granularity, not per index.

### Overwriting Outside the Recording Scope

If a recorded transient value is overwritten outside a `record_transient()` scope, QUAM treats that as a permanent write. It warns and removes the transient record:

```python
with machine.record_transient():
    readout = machine.qubits["q0"].resonator.operations["readout"]
    readout.amplitude = 0.2

readout.amplitude = 0.15  # warns; this value is now permanent

print(machine.get_transient_changes())
# []
```

After this happens, `revert_transient()` will not restore the old value for that path because the transient record has been removed.

### Scope and Limitations

- Nested `record_transient()` scopes are not supported and raise `RuntimeError`.
- Detached components are not recorded into the last instantiated root; only objects attached to the active root are tracked.
- Transient state is for runtime mutations. Use `skip_save` metadata for fields that should never be serialized, even when they are not transient.
