# QuAM Demonstration

## Introduction

This demonstration will guide you through setting up a basic superconducting quantum circuit using QuAM, applicable to various quantum platforms beyond superconducting setups.

## Setting Up

Start by importing the necessary components for a superconducting quantum circuit from QuAM's library:

```python
from quam.components import *
from quam.examples.superconducting_qubits import Transmon, QuAM
```

## Initialization

QuAM requires an initial setup where all components are instantiated. Create the root QuAM object, which acts as the top-level container for your quantum setup. Although `QuAM` is predefined, you're encouraged to define your own custom components for specialized needs:

```python
machine = QuAM()
```

Initially, `machine` is an empty container. You'll populate it with quantum circuit components, specifically Transmon qubits and associated resonators.

## Populating the Machine

Define the number of qubits and initialize them, along with their resonators:

```python
num_qubits = 2
for idx in range(num_qubits):
    transmon = Transmon(
        id=idx,
        xy=IQChannel(
            frequency_converter_up=FrequencyConverter(
                local_oscillator=LocalOscillator(power=10, frequency=6e9),
                mixer=Mixer(),
            ),
            opx_output_I=("con1", 3 * idx + 3),
            opx_output_Q=("con1", 3 * idx + 4),
        ),
        z=SingleChannel(opx_output=("con1", 3 * idx + 5)),
    )
    machine.qubits.append(transmon)

    resonator = InOutIQChannel(
        opx_input_I=("con1", 1),
        opx_input_Q=("con1", 2),
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        id=idx,
        frequency_converter_up=FrequencyConverter(
            local_oscillator=LocalOscillator(power=10, frequency=6e9),
            mixer=Mixer()
        )
    )
    machine.resonators.append(resonator)
```

This setup reflects QuAM's flexibility and the hierarchical structure of its component system where each component can be a parent or a child.

Absolutely! We'll add a section on attaching a `ReadoutPulse` to the resonator associated with the first qubit. This example will continue from the previous section on adding a Gaussian pulse to the qubit.

---

## Adding a Pulse to a Qubit and its Resonator

After configuring the qubits and resonators, you can further customize your setup by adding operational pulses. This example will show how to add a Gaussian pulse to the `xy` channel of a qubit and a `ReadoutPulse` to its resonator.

### Defining and Attaching the Pulses

#### Gaussian Pulse for Qubit Control

Define a basic Gaussian pulse for qubit manipulation and attach it to the `xy` channel of the first qubit:

```python
from quam.pulses import GaussianPulse

# Create a Gaussian pulse
gaussian_pulse = GaussianPulse(length=20, amplitude=0.5, sigma=3)

# Attach the pulse to the XY channel of the first qubit
machine.qubits[0].xy.add_pulse('X90', gaussian_pulse)
```

#### Readout Pulse for Qubit Resonator

Similarly, define a `ReadoutPulse` for the resonator associated with the same qubit to enable quantum state measurement:

```python
from quam.pulses import ReadoutPulse

# Create a Readout pulse
readout_pulse = ReadoutPulse(length=50, amplitude=0.7, digital_marker='ON')

# Attach the pulse to the resonator of the first qubit
machine.resonators[0].add_pulse('Readout', readout_pulse)
```

### Invoking the Pulses in a Function

With the pulses defined and attached, you can create functions to apply these pulses during your quantum operations:

```python
def apply_qubit_pulse(qubit):
    """
    Apply the 'X90' Gaussian pulse to the specified qubit's XY channel.
    """
    qubit.xy.play_pulse('X90')

def apply_readout_pulse(resonator):
    """
    Apply the 'Readout' pulse to the specified resonator.
    """
    resonator.play_pulse('Readout')

# Call the functions with the first qubit and its resonator
apply_qubit_pulse(machine.qubits[0])
apply_readout_pulse(machine.resonators[0])
```

### Explanation

In this example, the `apply_qubit_pulse` function triggers a control pulse on the qubit, essential for quantum operations such as gate applications. The `apply_readout_pulse` function, on the other hand, is crucial for reading out the state of the qubit through its resonator, which is a fundamental part of performing measurements in quantum experiments.


## Overview of Configuration

Display the current configuration of your QuAM setup:

```python
machine.print_summary()
```

The output provides a detailed hierarchical view of the machine's configuration, illustrating the connectivity and settings of each component.

## Persisting the Setup

Save the current state of your QuAM setup to a file for later use or inspection:

```python
machine.save("state.json")
```

The contents of `state.json` will mirror the structure and settings of your QuAM machine.

## Loading the Configuration

To resume work with a previously configured setup:

```python
loaded_machine = QuAM.load("state.json")
```

## Generating a QUA Configuration

Generate a QUA configuration from the current QuAM setup. This is essential for interfacing with quantum hardware:

```python
qua_config = machine.generate_config()
```

The resulting configuration is ready for use with QUA scripts to control quantum experiments.

```python
qm = qmm.open_qm(qua_config)  # Open a quantum machine with the configuration
```