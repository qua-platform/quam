# Migrating to QuAM

QuAM, the Quantum Abstract Machine, serves as a powerful abstraction framework built over the QUA programming language. This guide aims to facilitate a smooth transition for developers from QUA to QuAM by detailing the necessary steps and modifications.

## Overview of Migration Process

The migration from QUA to QuAM involves two primary stages:

1. **Conversion of the QUA Configuration to QuAM Components:** This step involves translating your existing QUA configurations into QuAM's component-based structure, starting from the root object down to individual channels and pulses.

2. **Creation of High-Level QuAM Components:** While optional, defining high-level components such as qubits can significantly enhance the manageability and scalability of your quantum programs by abstracting complex configurations.

## Step 1: Convert QUA Configuration to QuAM

### 1. Create a Root QuAM Object

Begin by establishing a `QuamRoot` object, which serves as the top-level container for all other QuAM components. For simplicity, you can use the pre-defined `BasicQuAM` class:

```python
from quam.components import BasicQuAM

machine = BasicQuAM()
machine.print_summary()
```
<!-- TODO Add output -->

Next we populate the root-level `machine` object with QuAM components

### Adding Octaves
If you have one or more Octave components, you can add them to the QUA configuration:
```python
from quam.components import Octave, OctaveUpConverter, OctaveDownConverter, Channel

machine.octaves["octave1"] = Octave(name="octave1", ip="127.0.0.1", port=80)

# Initialize all frequency converters using the default connectivity to the OPX
machine.octave.initialize_frequency_converters()
```
Refer to the [Octave documentation][octave] for further configuration details

### Convert "elements" to Channels
The QUA configuration has a section labelled `"elements"`, which corresponds to a pulse processor that can either send or receive signals.
Each element has a direct mapping to one of the [quam.components.channels][] in QuAM, though the channel type depends on the element.

Here we show how to convert different types of elements to QuAM channels.
We don't cover all possible properties, details for this can be found in the [Channels documentation][channels] and the relevant API documentation for each channel type.
We also delay the discussion on the `"operations"` field for the next section on pulses.

#### Single Analog Output Channel
In the simplest case, a single output channel is defined in the QUA configuration.


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

    machine.channels["qubit_z"] = IQChannel(
        opx_output=("con1", 1),
    )
    ```
  </div>
</div>

The corresponding QuAM component is the [SingleChannel][quam.components.SingleChannel].

#### IQ Analog Output Channel

In the case where the IQ channel is not connected to an


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
    from quam.components import IQChannel

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


If an Octave is used for upconversion, the IQChannel should be connected to the OctaveUpConverter.


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

#### Single Analog Output + Input Channel
In the case where the channel is both an input and output channel, the [InOutSingleChannel][quam.components.InOutSingleChannel] should be used.


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

#### IQ Analog Output + Input Channel
In the case where the channel is both an input and output channel with IQ (de)modulation, the [InOutIQChannel][quam.components.InOutIQChannel] should be used.


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


## Step 2: Create High-Level QuAM Components (Optional)
This step involves defining more abstract components such as qubits, which can simplify the interaction with the lower-level hardware details:

See [Custom components][custom-components] for more information on creating custom QuAM components.

## Conclusion

By following these steps, you should be able to transition your existing QUA codebase to the more flexible and powerful QuAM framework efficiently. 
Remember, the key to a successful migration is understanding the mapping of QUA elements to QuAM components and taking advantage of QuAM's modular design to enhance your quantum programming capabilities.