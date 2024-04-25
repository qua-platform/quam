# Migrating to QuAM

QuAM serves as an abstraction framework over the QUA programming language.
For users already familiar with QUA, transitioning to QuAM is straightforward.
In this guide, we outline the steps to migrate your existing QUA code to QuAM.

Assuming you already have a QUA configuration, the migration process involves two steps:

1. Migrate the **QUA configuration** to QuAM Use the standard QuAM components.
2. Create **high-level QuAM components** (e.g. qubit) that encapsulate the low-level components and build abstraction layers.  
  The second step is optional but can significantly help in organizing and simplifying your codebase.

## Migrate QUA Configuration to QuAM

### Create a Root QuAM Object
The QuAM structure needs a top-level [QuamRoot][quam.core.QuamRoot] which has features such as saving/loading QuAM.
Typically one would subclass [QuamRoot][quam.core.QuamRoot] and add the necessary components as fields.
However, as a basic example, we can use the [BasicQuAM][quam.components.BasicQuAM] class, which contains the fields necessary for the migration.
We call this object the `machine`.

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

# Initialize all frequency converters in the default wiring configuration
machine.octave.initialize_frequency_converters()
```
The [Octave documentation][octave] provides more details on the Octave configuration.

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

    machine.channels["readout_resonator"] = InOutSingleChannel(
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
    "qubit_xy": {
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

    machine.channels["qubit_xy"] = channel = IQChannel(
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


