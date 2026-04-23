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

## Temporary Values for a Calibration

Start from a loaded QUAM state and select the components involved in the calibration:

```python
machine = Quam.load()
qubits = [machine.qubits["q1"], machine.qubits["q2"]]
```

The exact component structure depends on your QUAM model. In this example, each qubit has a resonator with a readout pulse amplitude:

```python
with machine.record_transient():
    for qubit in qubits:
        qubit.resonator.readout_pulse.amplitude = max_readout_amplitude
```

`record_transient()` records the original values before the writes happen. It does not revert the values when the `with` block exits. The temporary values remain live on the machine:

```python
print(machine.qubits["q1"].resonator.readout_pulse.amplitude)
# max_readout_amplitude
```

This is the key behavior: the temporary values are available to normal QUAM access and config generation.

## Generate a Config With Temporary Values

After recording the temporary changes, generate the config as usual:

```python
config = machine.generate_config()
```

The generated config sees the temporary readout amplitudes because they are still live on the QUAM object. This lets the calibration run with the values needed for the experiment without making those values permanent.

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
        "path": "#/qubits/q1/resonator/readout_pulse/amplitude",
        "was": 0.05,
        "now": 0.2,
    },
    {
        "path": "#/qubits/q2/resonator/readout_pulse/amplitude",
        "was": 0.04,
        "now": 0.2,
    },
]
```

When the temporary values are no longer needed, revert them:

```python
machine.revert_transient()

print(machine.qubits["q1"].resonator.readout_pulse.amplitude)
# 0.05
print(machine.get_transient_changes())
# []
```

The machine is now back to the state it had before the temporary calibration changes.

## Save Only the Calibration Result

After the experiment and analysis, apply the values you actually want to persist using normal assignments:

```python
machine.revert_transient()

for qubit in qubits:
    qubit.resonator.readout_pulse.amplitude = fitted_amplitudes[qubit.name]

machine.save()
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
    machine.qubits["q1"].resonator.readout_pulse.amplitude = max_readout_amplitude

machine.save()
```

In this case, the saved state contains the original amplitude, not `max_readout_amplitude`.

This behavior is a guardrail. In calibration code, it is usually clearer to call `revert_transient()` explicitly before applying and saving the final fitted values.

If saving fails after QUAM has reverted the transient values, QUAM restores the transient live state and records before raising the original exception.

## Additional Details

### First Write Is Recorded

Only the first write to a given attribute, dictionary key, or list is recorded. Later writes update the live value, but the original `was` value remains the value that will be restored:

```python
with machine.record_transient():
    pulse = machine.qubits["q1"].resonator.readout_pulse
    pulse.amplitude = 0.1
    pulse.amplitude = 0.2

print(machine.get_transient_changes())
# [{"path": ".../amplitude", "was": 0.05, "now": 0.2}]
```

### Dictionaries and Lists

Transient recording also tracks writes through QUAM dictionaries and lists.

Dictionary mutations are recorded per key:

```python
with machine.record_transient():
    machine.metadata["temporary_mode"] = "power_sweep"
```

For added or deleted dictionary keys, `was` or `now` is the `MISSING` sentinel from `quam.core.transient`.

List mutations are recorded as a snapshot of the whole list:

```python
with machine.record_transient():
    machine.active_qubits.append("q3")

print(machine.get_transient_changes())
# [{"path": "#/active_qubits", "was": ["q1", "q2"], "now": ["q1", "q2", "q3"]}]
```

List changes are tracked at list granularity, not per index.

### Overwriting Outside the Recording Scope

If a recorded transient value is overwritten outside a `record_transient()` scope, QUAM treats that as a permanent write. It warns and removes the transient record:

```python
with machine.record_transient():
    pulse = machine.qubits["q1"].resonator.readout_pulse
    pulse.amplitude = 0.2

pulse.amplitude = 0.15  # warns; this value is now permanent

print(machine.get_transient_changes())
# []
```

After this happens, `revert_transient()` will not restore the old value for that path because the transient record has been removed.

### Scope and Limitations

- Nested `record_transient()` scopes are not supported and raise `RuntimeError`.
- Detached components are not recorded into the last instantiated root; only objects attached to the active root are tracked.
- Transient state is for runtime mutations. Use `skip_save` metadata for fields that should never be serialized, even when they are not transient.
