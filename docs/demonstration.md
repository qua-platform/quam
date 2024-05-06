# QuAM Demonstration

## Introduction

Welcome to our QuAM tutorial! This guide will demonstrate setting up a basic superconducting quantum circuit with two transmon qubits and their resonators. We'll equip these qubits with control and readout pulses and generate a QUA configuration for interacting with quantum hardware.

QuAM is not limited to any specific quantum hardware platform. It is designed to be adaptable and extensible for various quantum systems. You can customize components or expand the framework to add new functionalities as needed. For details on customization, visit [Custom QuAM Components](/components/custom-components).

We will first demonstrate how to create a basic QuAM setup from scratch. This is typically done once at the beginning of a project. Then, we'll show how to modify the setup, save the changes, and generate a QUA configuration for running quantum programs.

By the end of this tutorial, you'll know how to use QuAM effectively for setting up, controlling, and measuring quantum systems.


## Setting Up

Start by importing the necessary components for a superconducting quantum circuit from QuAM's library:

```python
from quam.components import *
from quam.examples.superconducting_qubits import Transmon, QuAM
```
As can be seen, we use transmon-specific components from `quam.examples.superconducting_qubits` to set up the quantum circuit.
Users are recommended to create their own custom components for specialized needs.

## Initialization

QuAM requires an initial setup where all components are instantiated. Create the root QuAM object, which acts as the top-level container for your quantum setup (see [QuAM Root Documentation](/components/quam-root) for details):

```python
machine = QuAM() # (1)

```

1.   The `QuAM` instance is called `machine` instead of `quam` to avoid conflicts with the statement `import quam`

Initially, `machine` is an empty container. You'll populate it with quantum circuit components, specifically Transmon qubits and associated resonators.

## Populating the Machine

Define the number of qubits and initialize them, along with their channels and resonators:

```python
num_qubits = 2
for idx in range(num_qubits):
    # Create transmon qubit component
    transmon = Transmon(id=idx)
    machine.qubits[transmon.name] = transmon

    # Add xy drive line channel
    transmon.xy = IQChannel(
        opx_output_I=("con1", 3 * idx + 3),
        opx_output_Q=("con1", 3 * idx + 4),
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(),
            local_oscillator=LocalOscillator(power=10, frequency=6e9),
        ),
        intermediate_frequency=100e6,
    )

    # Add transmon flux line channel
    transmon.z = SingleChannel(opx_output=("con1", 3 * idx + 5))
    
    # Add resonator channel
    transmon.resonator = InOutIQChannel(
        id=idx,
        opx_output_I=("con1", 3 * idx + 1),
        opx_output_Q=("con1", 3 * idx + 2),
        opx_input_I=("con1", 1),
        opx_input_Q=("con1", 2,),
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator(power=10, frequency=6e9)
        ),
    )
```

/// details | Autocomplete with IDEs
    type: tip
Code editors with Python language support (e.g., VS Code, PyCharm) are very useful here because they explain what attributes each class has, what the type should be, and docstrings. This makes it a breeze to create a QuAM from scratch.
///

This setup reflects QuAM's flexibility and the hierarchical structure of its component system where each component can be a parent or a child.

## Adding a Pulse to a Qubit and its Resonator

After configuring the qubits and resonators, you can further customize your setup by adding operational pulses. This example will show how to add a Gaussian pulse to the `xy` channel of a qubit and a `ReadoutPulse` to its resonator.

### Defining and Attaching the Pulses

#### Gaussian Pulse for Qubit Control

Define a basic Gaussian pulse for qubit manipulation and attach it to the `xy` channel of the first qubit:

```python
from quam.components.pulses import GaussianPulse

# Create a Gaussian pulse
gaussian_pulse = GaussianPulse(length=20, amplitude=0.2, sigma=3)

# Attach the pulse to the XY channel of the first qubit
machine.qubits["q0"].xy.operations["X90"] = gaussian_pulse
```

#### Readout Pulse for Qubit Resonator

Similarly, define a `SquareReadoutPulse` (constant in readout amplitude) for the resonator associated with the same qubit to enable quantum state measurement:

```python
from quam.components.pulses import SquareReadoutPulse

# Create a Readout pulse
readout_pulse = SquareReadoutPulse(length=1000, amplitude=0.1)

# Attach the pulse to the resonator of the first qubit
machine.qubits["q0"].resonator.operations["readout"] = readout_pulse
```

### Invoking the Pulses in a Function
```python
from qm.qua import program

with program() as prog:
    qubit = machine.qubits["q0"]

    # Apply the Gaussian pulse to the qubit
    qubit.xy.play("X90")

    # Perform readout on the qubit
    I, Q = qubit.resonator.measure("readout")
```


## Overview of Configuration

Display the current configuration of your QuAM setup:

```python
machine.print_summary()
```

/// details | `machine.print_summary()` output
```json
QuAM:
  qubits: QuamDict
    q0: Transmon
      id: 0
      xy: IQChannel
        operations: QuamDict
          X90: GaussianPulse
            length: 20
            id: None
            digital_marker: None
            amplitude: 0.2
            sigma: 3
            axis_angle: None
            subtracted: True
        id: None
        digital_outputs: QuamDict Empty
        opx_output_I: ('con1', 3)
        opx_output_Q: ('con1', 4)
        opx_output_offset_I: None
        opx_output_offset_Q: None
        frequency_converter_up: FrequencyConverter
          local_oscillator: LocalOscillator
            frequency: 6000000000.0
            power: 10
          mixer: Mixer
            local_oscillator_frequency: "#../local_oscillator/frequency"
            intermediate_frequency: "#../../intermediate_frequency"
            correction_gain: 0
            correction_phase: 0
          gain: None
        intermediate_frequency: 100000000.0
      z: SingleChannel
        operations: QuamDict Empty
        id: None
        digital_outputs: QuamDict Empty
        opx_output: ('con1', 5)
        filter_fir_taps: None
        filter_iir_taps: None
        opx_output_offset: None
        intermediate_frequency: None
      resonator: InOutIQChannel
        operations: QuamDict
          readout: SquareReadoutPulse
            length: 1000
            id: None
            digital_marker: "ON"
            amplitude: 0.1
            axis_angle: None
            threshold: None
            rus_exit_threshold: None
            integration_weights: None
            integration_weights_angle: 0
        id: 0
        digital_outputs: QuamDict Empty
        opx_output_I: ('con1', 1)
        opx_output_Q: ('con1', 2)
        opx_output_offset_I: None
        opx_output_offset_Q: None
        frequency_converter_up: FrequencyConverter
          local_oscillator: LocalOscillator
            frequency: 6000000000.0
            power: 10
          mixer: Mixer
            local_oscillator_frequency: "#../local_oscillator/frequency"
            intermediate_frequency: "#../../intermediate_frequency"
            correction_gain: 0
            correction_phase: 0
          gain: None
        intermediate_frequency: 0.0
        opx_input_I: ('con1', 1)
        opx_input_Q: ('con1', 2)
        time_of_flight: 24
        smearing: 0
        opx_input_offset_I: None
        opx_input_offset_Q: None
        input_gain: None
        frequency_converter_down: None
    q1: Transmon
      id: 1
      xy: IQChannel
        operations: QuamDict Empty
        id: None
        digital_outputs: QuamDict Empty
        opx_output_I: ('con1', 6)
        opx_output_Q: ('con1', 7)
        opx_output_offset_I: None
        opx_output_offset_Q: None
        frequency_converter_up: FrequencyConverter
          local_oscillator: LocalOscillator
            frequency: 6000000000.0
            power: 10
          mixer: Mixer
            local_oscillator_frequency: "#../local_oscillator/frequency"
            intermediate_frequency: "#../../intermediate_frequency"
            correction_gain: 0
            correction_phase: 0
          gain: None
        intermediate_frequency: 100000000.0
      z: SingleChannel
        operations: QuamDict Empty
        id: None
        digital_outputs: QuamDict Empty
        opx_output: ('con1', 8)
        filter_fir_taps: None
        filter_iir_taps: None
        opx_output_offset: None
        intermediate_frequency: None
      resonator: InOutIQChannel
        operations: QuamDict Empty
        id: 1
        digital_outputs: QuamDict Empty
        opx_output_I: ('con1', 4)
        opx_output_Q: ('con1', 5)
        opx_output_offset_I: None
        opx_output_offset_Q: None
        frequency_converter_up: FrequencyConverter
          local_oscillator: LocalOscillator
            frequency: 6000000000.0
            power: 10
          mixer: Mixer
            local_oscillator_frequency: "#../local_oscillator/frequency"
            intermediate_frequency: "#../../intermediate_frequency"
            correction_gain: 0
            correction_phase: 0
          gain: None
        intermediate_frequency: 0.0
        opx_input_I: ('con1', 1)
        opx_input_Q: ('con1', 2)
        time_of_flight: 24
        smearing: 0
        opx_input_offset_I: None
        opx_input_offset_Q: None
        input_gain: None
        frequency_converter_down: None
  wiring: QuamDict Empty
```
///

The output provides a detailed hierarchical view of the machine's configuration, illustrating the connectivity and settings of each component.

## Saving the QuAM Setup

Save the current state of your QuAM setup to a file for later use or inspection:

```python
machine.save("state.json")
```

/// details | state.json
```json
{
    "__class__": "quam.examples.superconducting_qubits.components.QuAM",
    "qubits": {
        "q0": {
            "id": 0,
            "resonator": {
                "frequency_converter_up": {
                    "__class__": "quam.components.hardware.FrequencyConverter",
                    "local_oscillator": {"frequency": 6000000000.0, "power": 10},
                    "mixer": {},
                },
                "id": 0,
                "operations": {
                    "readout": {
                        "__class__": "quam.components.pulses.SquareReadoutPulse",
                        "amplitude": 0.1,
                        "length": 1000,
                    }
                },
                "opx_input_I": ["con1", 1],
                "opx_input_Q": ["con1", 2],
                "opx_output_I": ["con1", 1],
                "opx_output_Q": ["con1", 2],
            },
            "xy": {
                "frequency_converter_up": {
                    "__class__": "quam.components.hardware.FrequencyConverter",
                    "local_oscillator": {"frequency": 6000000000.0, "power": 10},
                    "mixer": {},
                },
                "intermediate_frequency": 100000000.0,
                "operations": {
                    "X90": {
                        "__class__": "quam.components.pulses.GaussianPulse",
                        "amplitude": 0.2,
                        "length": 20,
                        "sigma": 3,
                    }
                },
                "opx_output_I": ["con1", 3],
                "opx_output_Q": ["con1", 4],
            },
            "z": {"opx_output": ["con1", 5]},
        },
        "q1": {
            "id": 1,
            "resonator": {
                "frequency_converter_up": {
                    "__class__": "quam.components.hardware.FrequencyConverter",
                    "local_oscillator": {"frequency": 6000000000.0, "power": 10},
                    "mixer": {},
                },
                "id": 1,
                "opx_input_I": ["con1", 1],
                "opx_input_Q": ["con1", 2],
                "opx_output_I": ["con1", 4],
                "opx_output_Q": ["con1", 5],
            },
            "xy": {
                "frequency_converter_up": {
                    "__class__": "quam.components.hardware.FrequencyConverter",
                    "local_oscillator": {"frequency": 6000000000.0, "power": 10},
                    "mixer": {},
                },
                "intermediate_frequency": 100000000.0,
                "opx_output_I": ["con1", 6],
                "opx_output_Q": ["con1", 7],
            },
            "z": {"opx_output": ["con1", 8]},
        },
    },
}
```
///

The contents of `state.json` will mirror the structure and settings of your QuAM machine.

## Loading the Configuration

To resume work with a previously configured setup:

```python
loaded_machine = QuAM.load("state.json")
```


## Workflow

Follow these steps for a typical execution flow in QuAM:

1. **Initialize a New QuAM Setup**: Start by generating a new QuAM configuration for your quantum system as demonstrated earlier, and save this initial setup to a file. This step sets the baseline for your system's configuration.
   
2. **Modify and Save**: Load the QuAM setup from the configuration file whenever you need to run new calibrations. After running your experiments and analyzing the results, you might need to adjust the configuration, such as updating pulse amplitudes based on your findings.

**Example of Updating Pulse Amplitude**: Suppose a calibration determines a new optimal pulse amplitude. You would update the pulse amplitude in your QuAM setup and save the changes back to the configuration file.

```python
# Load QuAM
machine = QuAM.load("state.json")

# Run QUA program and analyse results to extract the optimal pulse amplitude
results = some_qua_program()
pulse_amplitude = amplitude_analysis_function(results)

# Update the pulse amplitude for the relevant qubit
machine.qubits["q0"].xy.operations["X90"].amplitude = pulse_amplitude

# Save the updated QuAM configuration
machine.save("state.json")
```

This workflow ensures your QuAM setup remains current with the latest experimental adjustments, allowing for iterative enhancements and refinements based on empirical data.


## Generating a QUA Configuration

Generate a QUA configuration from the current QuAM setup. This is essential for interfacing with quantum hardware:

```python
qua_config = machine.generate_config()
```

/// details | qua_config
```json
{
    "controllers": {
        "con1": {
            "analog_inputs": {1: {"offset": 0.0}, 2: {"offset": 0.0}},
            "analog_outputs": {
                1: {"offset": 0.0},
                2: {"offset": 0.0},
                3: {"offset": 0.0},
                4: {"offset": 0.0},
                5: {"offset": 0.0},
                6: {"offset": 0.0},
                7: {"offset": 0.0},
                8: {"offset": 0.0},
            },
            "digital_outputs": {},
        }
    },
    "digital_waveforms": {"ON": {"samples": [[1, 0]]}},
    "elements": {
        "IQ0": {
            "intermediate_frequency": 0.0,
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": 6000000000.0,
                "mixer": "IQ0.mixer",
            },
            "operations": {"readout": "IQ0.readout.pulse"},
            "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
            "smearing": 0,
            "time_of_flight": 24,
        },
        "IQ1": {
            "intermediate_frequency": 0.0,
            "mixInputs": {
                "I": ("con1", 4),
                "Q": ("con1", 5),
                "lo_frequency": 6000000000.0,
                "mixer": "IQ1.mixer",
            },
            "operations": {},
            "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
            "smearing": 0,
            "time_of_flight": 24,
        },
        "q0.xy": {
            "intermediate_frequency": 100000000.0,
            "mixInputs": {
                "I": ("con1", 3),
                "Q": ("con1", 4),
                "lo_frequency": 6000000000.0,
                "mixer": "q0.xy.mixer",
            },
            "operations": {"X90": "q0.xy.X90.pulse"},
        },
        "q0.z": {"operations": {}, "singleInput": {"port": ("con1", 5)}},
        "q1.xy": {
            "intermediate_frequency": 100000000.0,
            "mixInputs": {
                "I": ("con1", 6),
                "Q": ("con1", 7),
                "lo_frequency": 6000000000.0,
                "mixer": "q1.xy.mixer",
            },
            "operations": {},
        },
        "q1.z": {"operations": {}, "singleInput": {"port": ("con1", 8)}},
    },
    "integration_weights": {
        "IQ0.readout.iw1": {"cosine": [(1.0, 1000)], "sine": [(-0.0, 1000)]},
        "IQ0.readout.iw2": {"cosine": [(0.0, 1000)], "sine": [(1.0, 1000)]},
        "IQ0.readout.iw3": {"cosine": [(-0.0, 1000)], "sine": [(-1.0, 1000)]},
    },
    "mixers": {
        "IQ0.mixer": [
            {
                "correction": [1.0, 0.0, 0.0, 1.0],
                "intermediate_frequency": 0.0,
                "lo_frequency": 6000000000.0,
            }
        ],
        "IQ1.mixer": [
            {
                "correction": [1.0, 0.0, 0.0, 1.0],
                "intermediate_frequency": 0.0,
                "lo_frequency": 6000000000.0,
            }
        ],
        "q0.xy.mixer": [
            {
                "correction": [1.0, 0.0, 0.0, 1.0],
                "intermediate_frequency": 100000000.0,
                "lo_frequency": 6000000000.0,
            }
        ],
        "q1.xy.mixer": [
            {
                "correction": [1.0, 0.0, 0.0, 1.0],
                "intermediate_frequency": 100000000.0,
                "lo_frequency": 6000000000.0,
            }
        ],
    },
    "oscillators": {},
    "pulses": {
        "IQ0.readout.pulse": {
            "digital_marker": "ON",
            "integration_weights": {
                "iw1": "IQ0.readout.iw1",
                "iw2": "IQ0.readout.iw2",
                "iw3": "IQ0.readout.iw3",
            },
            "length": 1000,
            "operation": "measurement",
            "waveforms": {"I": "IQ0.readout.wf.I", "Q": "IQ0.readout.wf.Q"},
        },
        "const_pulse": {
            "length": 1000,
            "operation": "control",
            "waveforms": {"I": "const_wf", "Q": "zero_wf"},
        },
        "q0.xy.X90.pulse": {
            "length": 20,
            "operation": "control",
            "waveforms": {"I": "q0.xy.X90.wf.I", "Q": "q0.xy.X90.wf.Q"},
        },
    },
    "version": 1,
    "waveforms": {
        "IQ0.readout.wf.I": {"sample": 0.1, "type": "constant"},
        "IQ0.readout.wf.Q": {"sample": 0.0, "type": "constant"},
        "const_wf": {"sample": 0.1, "type": "constant"},
        "q0.xy.X90.wf.I": {
            "samples": array(
                [
                    0.0,
                    0.0022836,
                    0.00745838,
                    0.01779789,
                    0.03592509,
                    0.06360149,
                    0.09993812,
                    0.14000065,
                    0.17517038,
                    0.19591242,
                    0.19591242,
                    0.17517038,
                    0.14000065,
                    0.09993812,
                    0.06360149,
                    0.03592509,
                    0.01779789,
                    0.00745838,
                    0.0022836,
                    0.0,
                ]
            ),
            "type": "arbitrary",
        },
        "q0.xy.X90.wf.Q": {
            "samples": array(
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ]
            ),
            "type": "arbitrary",
        },
        "zero_wf": {"sample": 0.0, "type": "constant"},
    },
}

 ```
///

The resulting configuration is ready for use with QUA scripts to control quantum experiments.

```python
qm = qmm.open_qm(qua_config)  # Open a quantum machine with the configuration
```