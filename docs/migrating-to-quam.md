# Migrating to QuAM

QuAM, the Quantum Abstract Machine, serves as a powerful abstraction framework built over the QUA programming language. This guide aims to facilitate a smooth transition for developers from QUA to QuAM by detailing the necessary steps and modifications.

## Overview of Migration Process

Migrating from QUA to QuAM involves a structured, five-step process that methodically transitions your existing quantum programming framework. Here's a brief overview of each step:

1. **Create a Root QuAM Object:** Start by establishing a foundational [QuamRoot][quam.core.quam_classes.QuamRoot] object that serves as the top-level container for all other QuAM components. This is where you'll begin building your new QuAM configuration.

2. **Add Octaves:** If your original QUA setup includes Octave components, this step involves integrating these components into the QuAM configuration, utilizing existing connectivity settings.

3. **Convert "elements" to Channels:** Each element in the QUA configuration that handles signal processing is mapped to a corresponding channel type in QuAM. This critical step ensures that the functional properties of your setup are preserved and adapted to the new architecture.

4. **Convert Pulses:** After setting up the channels, the next step is to configure the pulses. This involves translating QUA pulse specifications into QuAM's consolidated and parameterized pulse framework.

5. **Generate the QUA configuration:** Once the QuAM structure has been created and populated, you can generate the QUA configuration using the QuAM object. This configuration can then be used to run quantum programs on the OPX.

5. **Create High-Level QuAM Components (Optional):** This final step is about abstracting complex configurations into high-level components like qubits, which can simplify the management and scalability of your quantum programs.

Each of these steps is designed to ensure a seamless transition to QuAM, leveraging its robust abstraction capabilities to manage and organize your quantum computing elements more effectively.

## 1: Create a Root QuAM Object

Begin by establishing a [QuamRoot][quam.core.quam_classes.QuamRoot] object, which serves as the top-level container for all other QuAM components. For simplicity, you can use the pre-defined [BasicQuAM][quam.components.basic_quam.BasicQuAM] class:

```python
from quam.components import BasicQuAM

machine = BasicQuAM()
machine.print_summary()  # outputs the current QuAM state
```

```title="output"
QuAM:
  channels: QuamDict Empty
  octaves: QuamDict Empty
```

Next we populate the root-level `machine` object with QuAM components

## 2: Add Octaves
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

## 4: Convert Pulses

After converting elements into channels, the next step is to configure the pulses. Pulses in QUA are defined across several fields within the configuration, each contributing to how the pulse is shaped and controlled. In QuAM, these properties are consolidated, allowing for a more streamlined and parameterized approach to pulse definition.

### Overview of QUA Pulse Configuration

In the QUA configuration, pulses are defined through the following components:

- **"waveforms"**: These are the actual waveform shapes labeled for reference within pulses.
- **"digital_waveforms"**: Digital signals that can be paired with analog waveforms to control pulse execution.
- **"integration_weights"**: Used for defining how signals are integrated during readout.
- **"pulses"**: This is a collection of pulse definitions, specifying labels, duration, and type of operation (`"control"` or `"measurement"`). Pulses may reference waveforms, digital waveforms, and integration weights specified in the other fields.
- **element["operations"]**: Maps operation names to specific pulses defined in the `"pulses"` collection, linking them to the relevant channel.

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


## 5: Generate the QUA configuration
Once the QUA configuration has been converted to QuAM, QuAM can in turn be used to generate the QUA configuration:

```python
qua_config = machine.generate_config()
```

This `qua_config` can then be used to create a `QuantumMachine` object, which can be used to run quantum programs on the OPX.

## 6: Create High-Level QuAM Components (Optional)
After converting the QUA configuration to the corresponding QuAM components, an optional next step is to group similar components into higher-level abstractions.
As an example, in the code above we had multiple channels belonging to the same qubit (`qubit_xy`, `qubit_z`, `qubit_readout`).
We can group these channels into a single `Qubit` object to simplify the management of the qubit's configuration:

```python
from quam.core import QuamComponent, quam_dataclass
from quam.components import SingleChannel, IQChannel, InOutSingleChannel

@quam_dataclass
class Qubit(QuamComponent):
    xy: IQChannel
    z: SingleChannel
    readout: InOutSingleChannel

qubit = Qubit(xy=qubit_xy, z=qubit_z, readout=qubit_readout)
```

This `Qubit` object can then be used to access the individual channels and their associated pulses, simplifying the management of the qubit's configuration.

Note that the root-level QuAM object also needs to be customized to support the new `Qubit` object:
```python
from typing import Dict
from quam.core import QuamRoot

@quam_dataclass
class QuAM(QuamRoot):
    qubits: Dict[str, Qubit]

machine = QuAM(qubits={"qubit1": qubit})
```

See [Custom QuAM Components](/components/custom-components) for more information on creating custom QuAM components.

## Conclusion

Following these steps will guide you through transitioning your existing QUA codebase to QuAM. The primary goal of this migration is to harness QuAM's abstraction capabilities to organize and manage the underlying quantum-computing elements. QuAM provides a structured way to encapsulate the complexity of your configurations, which can facilitate maintenance and scalability. By understanding the mapping of QUA elements to QuAM components, you can effectively utilize this abstraction layer to enhance the organization of your quantum programs.
