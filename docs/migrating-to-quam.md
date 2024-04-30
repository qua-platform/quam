# Migrating to QuAM

QuAM, the Quantum Abstract Machine, serves as a powerful abstraction framework built over the QUA programming language. This guide aims to facilitate a smooth transition for developers from QUA to QuAM by detailing the necessary steps and modifications.

## Overview of Migration Process

The migration from QUA to QuAM involves five steps:

1. **Conversion of the QUA Configuration to QuAM Components:** This step involves translating your existing QUA configurations into QuAM's component-based structure, starting from the root object down to individual channels and pulses.

2. **Creation of High-Level QuAM Components:** While optional, defining high-level components such as qubits can significantly enhance the manageability and scalability of your quantum programs by abstracting complex configurations.

<!-- ## Step 1: Convert QUA Configuration to QuAM -->

## 1: Create a Root QuAM Object

Begin by establishing a `QuamRoot` object, which serves as the top-level container for all other QuAM components. For simplicity, you can use the pre-defined `BasicQuAM` class:

```python
from quam.components import BasicQuAM

machine = BasicQuAM()
machine.print_summary()  # outputs the current QuAM state
```
<!-- TODO Add output -->

Next we populate the root-level `machine` object with QuAM components

## 2: Adding Octaves
If you have one or more Octave components, you can add them to the QUA configuration:
```python
from quam.components import Octave

machine.octaves["octave1"] = Octave(name="octave1", ip="127.0.0.1", port=80)

# Initialize all frequency converters using the default connectivity to the OPX
machine.octave.initialize_frequency_converters()
```
Refer to the [Octave documentation][octave] for further configuration details

## 3: Convert "elements" to Channels
The QUA configuration has a section labelled `"elements"`, which corresponds to a pulse processor that can send and/or receive signals. 
Each element has a direct mapping to one of the [quam.components.channels][] in QuAM, though the channel type depends on the element.

Here we show how to convert different types of elements to QuAM channels. 
We don't cover all possible properties; details for this can be found in the [Channels documentation][channels] and the relevant API documentation for each channel type. 
We also postpone the discussion on the `"operations"` field for the next section on pulses.

### Single Analog Output Channel
For straightforward configurations with only a single output port, use the [SingleChannel][quam.components.SingleChannel] in QuAM. This example demonstrates the conversion of a single output setup in QUA to a SingleChannel in QuAM:

<div class="code-flex-container">
  <div class="code-flex-item">
    ```json title='qua_configuration["elements"]'
    "qubit_z": {
        "singleInput": {"port": ("con1", 1)},
        "operations": {...}
    }
    ```
  </div>
  <div class="code-flex-item">
    ```python title="QuAM"
    from quam.components import SingleChannel

    machine.channels["qubit_z"] = SingleChannel(
        opx_output=("con1", 1),
    )
    ```
  </div>
</div>


### IQ Analog Output Channel

When dealing with IQ modulation, the IQChannel provides the necessary framework. Below are examples of converting an element with IQ outputs and a frequency upconverter:

<div class="code-flex-container">
  <div class="code-flex-item">
    ```json title='qua_configuration["elements"]'
    "qubit_xy": {
        "intermediate_frequency": 100e6,
        "mixInputs": {
            "I": ("con1", 1),
            "Q": ("con1", 2),
            "lo_frequency": 5e9,
            "mixer": "mixer_qubit",
        },
        "operations": {...}
    },
    ```
  </div>
  <div class="code-flex-item">
    ```python title="QuAM"
    from quam.components import IQChannel, FrequencyConverter, LocalOscillator, Mixer

    channels["qubit_XY"] = IQChannel(
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=FrequencyConverter(
            local_oscillator=LocalOscillator(frequency=5e9),
            mixer=Mixer()
        )
    )
    ```
  </div>
</div>

If an Octave is used for upconversion, the [IQChannel][quam.components.IQChannel] should be connected to the [OctaveUpConverter][quam.components.octave.OctaveUpConverter].

<div class="code-flex-container">
  <div class="code-flex-item">
    ```json title='qua_configuration["elements"]'
    "qubit_xy": {
        "intermediate_frequency": 100e6,
        "RF_inputs": {"port": ["octave1", 1]},
        "operations": {...}
    },
    ```
  </div>
  <div class="code-flex-item">
    ```python title="QuAM"
    from quam.components import IQChannel

    # Note the output/input is switched w.r.t. the QUA configuration
    RF_output = machine.octaves["octave1"].RF_outputs[1]

    machine.channels["qubit_xy"] = channel = IQChannel(
        opx_output_I=("con1", 1), 
        opx_output_Q=("con1", 2),
        frequency_converter_up=RF_output.get_reference()
    )
    RF_output.channel = channel.get_reference()
    ```
  </div>
</div>

Detailed instructions can be found at the [Octave documentation][octave].

### Single Analog Output + Input Channel

For elements that function as both input and output channels, use [InOutSingleChannel][quam.components.InOutSingleChannel]. This setup allows for efficient bidirectional communication:

<div class="code-flex-container">
  <div class="code-flex-item">
    ```json title='qua_configuration["elements"]'
    "qubit_readout": {
        "singleInput": {
            "port": ("con1", 1),
        },
        "outputs": {"out1": ("con1", 2)},
        "operations": {...}
    }
    ```
  </div>
  <div class="code-flex-item">
    ```python title="QuAM"
    from quam.components import InOutSingleChannel

    machine.channels["qubit_readout"] = InOutSingleChannel(
        opx_output=("con1", 1),
        opx_input=("con1", 2),
    )
    ```
  </div>
</div>

### IQ Analog Output + Input Channel
For complex setups involving both IQ modulation and bidirectional communication, the [InOutIQChannel][quam.components.InOutIQChannel] is the appropriate choice:

<div class="code-flex-container">
  <div class="code-flex-item">
    ```json title='qua_configuration["elements"]'
    "readout_resonator": {
        "intermediate_frequency": 100e6,
        "RF_inputs": {"port": ["octave1", 1]},
        "RF_outputs": {"port": ["octave1", 1]},
        "operations": {...}
    },
    ```
  </div>
  <div class="code-flex-item">
    ```python title="QuAM"
    from quam.components import IQChannel

    # Note the output/input is switched w.r.t. the QUA configuration
    RF_output = machine.octaves["octave1"].RF_outputs[1]
    RF_input = machine.octaves["octave1"].RF_inputs[2]

    machine.channels["readout_resonator"] = channel = IQChannel(
        opx_output_I=("con1", 1), 
        opx_output_Q=("con1", 2),
        opx_input_I=("con1", 1),
        opx_input_Q=("con1", 2),
        frequency_converter_up=RF_output.get_reference()
        frequency_converter_down=RF_input.get_reference()
    )
    RF_output.channel = channel.get_reference()
    ```
  </div>
</div>

## 4: Converting Pulses

After converting elements into channels, the next step is to configure the pulses. Pulses in QUA are defined across several fields within the configuration, each contributing to how the pulse is shaped and controlled. In QuAM, these properties are consolidated, allowing for a more streamlined and parameterized approach to pulse definition.

### Overview of QUA Pulse Configuration

In the QUA configuration, pulses are defined through the following components:

- **"waveforms"**: These are the actual waveform shapes labeled for reference within pulses.
- **"digital_waveforms"**: Digital signals that can be paired with analog waveforms to control pulse execution.
- **"integration_weights"**: Used for defining how signals are integrated during readout.
- **"pulses"**: This is a collection of pulse definitions, specifying labels, duration, and type of operation (`"control"` or `"measurement"`). Pulses may reference waveforms, digital waveforms, and integration weights specified in the other fields.
- **`element["operations"]`**: Maps operation names to specific pulses defined in the `"pulses"` collection, linking them to the relevant channel.

### QuAM Pulse Configuration

In QuAM, pulse properties are grouped and parameterized by pulse type, simplifying the configuration process. Here is how you would convert a typical pulse setup from QUA to QuAM:

#### Example: Converting a Constant Voltage Pulse

Consider a QUA pulse configured to deliver a constant voltage. In QuAM, this corresponds to the [SquarePulse][quam.components.pulses.SquarePulse] component, which is designed for straightforward amplitude modulation.

**QUA Configuration:**

```json
{
    "elements": {
        "qubit_xy": {
            "intermediate_frequency": 100e6,
            "mixInputs": {
                "I": ["con1", 1],
                "Q": ["con1", 2],
                "lo_frequency": 5e9,
                "mixer": "mixer_qubit"
            },
            "operations": {
                "const_pulse": "const_pulse"
            }
        }
    },
    "pulses": {
        "const_pulse": {
            "operation": "control",
            "length": 1000,
            "waveforms": {"I": "const_wf", "Q": "zero_wf"}
        }
    },
    "waveforms": {
        "const_wf": {"type": "constant", "sample": 0.5},
        "zero_wf": {"type": "constant", "sample": 0.0}
    }
}
```

**QuAM Conversion:**

```python
from quam.components import pulses

# Assuming qubit_xy is configured as an IQChannel
qubit_xy.operations["const_pulse"] = pulses.SquarePulse(
    length=1000,
    amplitude=0.5,
    axis_angle=0  # Phase angle on the IQ plane
)
```

This example highlights the transformation of a basic pulse from QUA into a QuAM `SquarePulse`, demonstrating the streamlined approach QuAM offers for pulse configuration.

For comprehensive details on configuring different types of pulses in QuAM, refer to the [Pulses Documentation][pulses].


## 5: Create High-Level QuAM Components (Optional)
After converting the QUA configuration 
This step involves defining more abstract components, which can simplify the interaction with the lower-level hardware details.

See [Custom components][custom-components] for more information on creating custom QuAM components.

## Conclusion

Following these steps will guide you through transitioning your existing QUA codebase to QuAM. The primary goal of this migration is to harness QuAM's abstraction capabilities to organize and manage the underlying quantum-computing elements. QuAM provides a structured way to encapsulate the complexity of your configurations, which can facilitate maintenance and scalability. By understanding the mapping of QUA elements to QuAM components, you can effectively utilize this abstraction layer to enhance the organization of your quantum programs.
