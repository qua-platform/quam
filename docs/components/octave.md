# Octave

An Octave is represented in QuAM through the [quam.components.octave.Octave][] class.
Below we describe the three steps needed to configuring an Octave in QuAM:

1. Creating the Octave
2. Adding frequency converters
3. Attaching channels

## :zero: Creating the Root QuAM Machine
Before we get started, we need a top-level QuAM class that matches our components:

```python
from typing import Dict
from dataclasses import field
from quam.core import QuamRoot, quam_dataclass
from quam.components import Octave, OctaveUpConverter, OctaveDownConverter, Channel

@quam_dataclass
class QuAM(QuamRoot):
    octave: Octave = None
    channels: Dict[str, Channel] = field(default_factory=dict)

machine = QuAM()
```

This will be used later to generate our QUA configuration

## :one: Creating the Octave
Below we show how an Octave is instantiated using some example arguments:

```python
octave = Octave(name="octave1", ip="127.0.0.1", port=80)
machine.octave = octave
```

We can next retrieve the Octave config `QmOctaveConfig`, used to create the `QuantumMachinesManager`
```python
octave_config = octave.get_octave_config()
# The calibration_db and device_info are automatically configured

qmm = QuantumMachinesManager(host={opx_host}, port={opx_port}, octave=octave_config)
```

At this point the channel connectivity of the Octave hasn't yet been configured.
We can do so by adding frequency converters.

## :two: Adding Frequency Converters
A frequency converter is a grouping of the components needed to upconvert or downconvert a signal.
These typically consist of a local oscillator, mixer, as well as IF, LO, and RF ports.
For the Octave we have two types of frequency converters:

- [OctaveUpConverter][quam.components.octave.OctaveUpConverter]: Used to upconvert a pair of IF signals to an RF signal
- [OctaveDownConverter][quam.components.octave.OctaveDownConverter]: Used to downconvert an RF signal to a pair of IF signals

We can add all relevant frequency converters as follows:

```python
octave.initialize_frequency_converters()

octave.print_summary()
```

/// details | `octave.print_summary()` output
```json
Octave (parent unknown):
  name: "octave1"
  ip: "127.0.0.1"
  port: 80
  calibration_db_path: None
  RF_outputs: QuamDict
    1: OctaveUpConverter
      id: 1
      channel: None
      LO_frequency: None
      LO_source: "internal"
      gain: 0
      output_mode: "always_off"
      input_attenuators: "off"
    2: OctaveUpConverter
      id: 2
      channel: None
      LO_frequency: None
      LO_source: "internal"
      gain: 0
      output_mode: "always_off"
      input_attenuators: "off"
    3: OctaveUpConverter
      id: 3
      channel: None
      LO_frequency: None
      LO_source: "internal"
      gain: 0
      output_mode: "always_off"
      input_attenuators: "off"
    4: OctaveUpConverter
      id: 4
      channel: None
      LO_frequency: None
      LO_source: "internal"
      gain: 0
      output_mode: "always_off"
      input_attenuators: "off"
    5: OctaveUpConverter
      id: 5
      channel: None
      LO_frequency: None
      LO_source: "internal"
      gain: 0
      output_mode: "always_off"
      input_attenuators: "off"
  RF_inputs: QuamDict
    1: OctaveDownConverter
      id: 1
      channel: None
      LO_frequency: None
      LO_source: "internal"
      IF_mode_I: "direct"
      IF_mode_Q: "direct"
      IF_output_I: 1
      IF_output_Q: 2
    2: OctaveDownConverter
      id: 2
      channel: None
      LO_frequency: None
      LO_source: "internal"
      IF_mode_I: "direct"
      IF_mode_Q: "direct"
      IF_output_I: 1
      IF_output_Q: 2
  loopbacks: QuamList = []
```
///

We can see five `OctaveUpConverter` elements in `Octave.RF_outputs`, and two `OctaveDownConverter` elements in `Octave.RF_inputs`, matching with the number of RF outputs / inputs, respectively.
It is important to specify the `LO_frequency` of the frequency converters that are used, otherwise they will not add information to the QUA configuration when it is generated.

At this point, our `Octave` does not yet contain any information on which OPX output / input is connected to each `OctaveUpconverter` / `OctaveDownConverter`.
This is done in the third stage

## :three: Attaching Channels
Once the frequency converters have been setup, it is time to attach the ones that are in use to corresponding channels in QuAM.
In the example below, we connect an `IQChannel` to the `OctaveUpconverter` at `octave.RF_outputs[1]`
```python
from quam.components import IQChannel, InOutIQChannel

machine.channels["IQ1"] = IQChannel(
    opx_output_I=("con1", 1), 
    opx_output_Q=("con1", 2),
    frequency_converter_up=octave.RF_outputs[1].get_reference()
)
octave.RF_outputs[1].channel = machine.channels["IQ1"].get_reference()
octave.RF_outputs[1].LO_frequency = 2e9  # Remember to set the LO frequency
```

Similarly, we can connect an `InOutIQChannel` to a combination of an `OctaveUpConverter` and `OctaveDownConverter`
```python
machine.channels["IQ2"] = InOutIQChannel(
    opx_output_I=("con1", 3), 
    opx_output_Q=("con1", 4),
    opx_input_I=("con1", 1),
    opx_input_Q=("con1", 2),
    frequency_converter_up=octave.RF_outputs[2].get_reference(),
    frequency_converter_down=octave.RF_inputs[1].get_reference()
)
octave.RF_outputs[2].channel = machine.channels["IQ2"].get_reference()
octave.RF_inputs[1].channel = machine.channels["IQ2"].get_reference()
octave.RF_outputs[2].LO_frequency = 2e9
octave.RF_inputs[2].LO_frequency = 2e9
```

## Generating the Config
Once everything is setup, we can generate the QUA configuration

```python
qua_config = machine.generate_config()
```

/// details | qua_config
```json
{
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                "1": {"offset": 0.0},
                "2": {"offset": 0.0},
                "3": {"offset": 0.0},
                "4": {"offset": 0.0},
            },
            "digital_outputs": {},
            "analog_inputs": {"1": {"offset": 0.0}, "2": {"offset": 0.0}},
        }
    },
    "elements": {
        "IQ1": {
            "operations": {},
            "intermediate_frequency": 0.0,
            "RF_inputs": {"port": ["octave1", 1]},
        },
        "IQ2": {
            "operations": {},
            "intermediate_frequency": 0.0,
            "RF_inputs": {"port": ["octave1", 2]},
            "smearing": 0,
            "time_of_flight": 24,
            "RF_outputs": {"port": ["octave1", 1]},
        },
    },
    "pulses": {
        "const_pulse": {
            "operation": "control",
            "length": 1000,
            "waveforms": {"I": "const_wf", "Q": "zero_wf"},
        }
    },
    "waveforms": {
        "zero_wf": {"type": "constant", "sample": 0.0},
        "const_wf": {"type": "constant", "sample": 0.1},
    },
    "digital_waveforms": {"ON": {"samples": [[1, 0]]}},
    "integration_weights": {},
    "mixers": {},
    "oscillators": {},
    "octaves": {
        "octave1": {
            "RF_outputs": {
                "1": {
                    "LO_frequency": 2000000000.0,
                    "LO_source": "internal",
                    "gain": 0,
                    "output_mode": "always_off",
                    "input_attenuators": "off",
                    "I_connection": ["con1", 1],
                    "Q_connection": ["con1", 2],
                },
                "2": {
                    "LO_frequency": 2000000000.0,
                    "LO_source": "internal",
                    "gain": 0,
                    "output_mode": "always_off",
                    "input_attenuators": "off",
                    "I_connection": ["con1", 3],
                    "Q_connection": ["con1", 4],
                },
            },
            "IF_outputs": {
                "IF_out1": {"port": ["con1", 1], "name": "out1"},
                "IF_out2": {"port": ["con1", 2], "name": "out2"},
            },
            "RF_inputs": {
                "1": {
                    "RF_source": "RF_in",
                    "LO_frequency": 2000000000.0,
                    "LO_source": "internal",
                    "IF_mode_I": "direct",
                    "IF_mode_Q": "direct",
                }
            },
            "loopbacks": [],
        }
    },
}

```
///

## Combined Example
```python
from typing import Dict
from dataclasses import field
from quam.core import QuamRoot, quam_dataclass
from quam.components import Octave, OctaveUpConverter, OctaveDownConverter, Channel

@quam_dataclass
class QuAM(QuamRoot):
    octave: Octave = None
    channels: Dict[str, Channel] = field(default_factory=dict)

machine = QuAM()


octave = Octave(
    name="octave1",
    ip="127.0.0.1",
    port=80,
)
machine.octave = octave

octave.initialize_frequency_converters()

octave.print_summary()


from quam.components import IQChannel, InOutIQChannel

machine.channels["IQ1"] = IQChannel(
    opx_output_I=("con1", 1), 
    opx_output_Q=("con1", 2),
    frequency_converter_up=octave.RF_outputs[1].get_reference()
)
octave.RF_outputs[1].channel = machine.channels["IQ1"].get_reference()
octave.RF_outputs[1].LO_frequency = 2e9


machine.channels["IQ2"] = InOutIQChannel(
    opx_output_I=("con1", 3), 
    opx_output_Q=("con1", 4),
    opx_input_I=("con1", 1),
    opx_input_Q=("con1", 2),
    frequency_converter_up=octave.RF_outputs[2].get_reference(),
    frequency_converter_down=octave.RF_inputs[1].get_reference()
)
octave.RF_outputs[2].channel = machine.channels["IQ2"].get_reference()
octave.RF_inputs[1].channel = machine.channels["IQ2"].get_reference()
octave.RF_outputs[2].LO_frequency = 2e9
octave.RF_inputs[1].LO_frequency = 2e9


qua_config = machine.generate_config()
```
