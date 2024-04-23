# Channels

In the QuAM library, channels are a fundamental concept that represent the physical connections to the quantum hardware. They are defined in the `quam.components.channels` module.

We distinguish between the following channel types:

**1. Analog output channels**

- [SingleChannel][quam.components.channels.SingleChannel]: Represents a single OPX output channel.
- [IQChannel][quam.components.IQChannel]: Represents an IQ OPX output channel.

**2. Analog output + input channels**

- [InOutSingleChannel][quam.components.channels.InOutSingleChannel]: Represents a single OPX output + input channel.
- [InOutIQChannel][quam.components.channels.InOutIQChannel]: Represents an IQ OPX output + input channel.

**3. Digital channels**  

- [DigitalOutputChannel][quam.components.channels.DigitalOutputChannel]: Represents a digital output channel.

Each analog [Channel][quam.components.channels.Channel] corresponds to an element in QUA, whereas the digital channel is part of an analog channel.

Note that in QuAM, the terms "output" and "input" are always from the perspective of the OPX hardware.

These channel combinations cover most use cases, although there are exceptions (input-only channels and single-output, IQ-input channels) which will be implemented in a subsequent QuAM release. If you need such channels, please create a [Github issue](https://github.com/qua-platform/quam/issues).

## Analog output channels

Analog output channels are the primary means of controlling the quantum hardware. They can be used to send various types of signals, such as microwave or RF signals, to control the quantum system. The two types of analog output channels are the [SingleChannel][quam.components.channels.SingleChannel] and the [IQChannel][quam.components.channels.IQChannel]. 

### Analog channel ports

A [SingleChannel][quam.components.channels.SingleChannel] is always attached to a single OPX output port, and similarly an [IQChannel][quam.components.channels.IQChannel] has an associated pair of IQ ports:


### DC offset
Each analog channel can have a specified DC offset that remains for the duration of the QUA program.
This can be set through `SingleChannel.opx_output_offset` for the `SingleChannel`, and through `IQChannel.opx_output_offset_I` and `IQChannel.opx_output_offset_Q` for the `IQChannel`.

Note that if multiple channels are attached to the same OPX output port(s), they may not have different output offsets.
This raises a warning and chooses the DC offset of the last channel. 

### Frequency converters
The `IQChannel` is usually connected to a mixer to upconvert the signal using a local oscillator.
This frequency upconversion is represented in QuAM by a [FrequencyConverter][quam.components.hardware.FrequencyConverter]

```python
from quam.components.hardware import FrequencyConverter, LocalOscillator, Mixer

IQ_channel = IQChannel(
    opx_output_I=("con1", 2),
    opx_output_Q=("con1", 3),
    frequency_converter=FrequencyConverter(
        local_oscillator=LocalOscillator(frequency=6e9, power=10),
        mixer=Mixer(),
    )
)
```

Integrated frequency conversion systems such as [QM's Octave](https://docs.quantum-machines.co/1.1.7/qm-qua-sdk/docs/Hardware/octave/) usually have additional features such as auto-calibration.
For this reason they have a specialized frequency converter such as the [OctaveUpConverter][quam.components.octave.OctaveUpConverter].
See the [octave][] documentation for details.

### Adding pulses to channels
QuAM has a range of standard pulses in [quam.components.pulses][quam.components.pulses].
These pulses can be registered as part of the analog channel via `Channel.operations` such that the channel can output the associated pulse waveforms:

```python
from quam.components import pulses

channel.operations["X180"] = pulses.SquarePulse(
    amplitude=0.1,  # Volt
    length=16,  # nanoseconds
)
```
### Playing pulses on a channel

## Analog output + input channels

### Readout pulses

## Digital channels
QuAM supports digital output channels (output from the OPX perspective) through the component [DigitalOutputChannel][quam.components.channels.DigitalOutputChannel].
These can be added to any analog channel through the attribute `Channel.digital_outputs`. As an example:

```python
from quam.components import SingleChannel, DigitalOutputChannel

analog_channel = SingleChannel(
    opx_output=("con1", 1),
    digital_outputs={
        "dig_out1": DigitalOutputChannel(opx_output=("con1", 1))
    }
)
```
The docstring of [DigitalOutputChannel][quam.components.channels.DigitalOutputChannel] describes all the available properties.

Multiple digital outputs can be attached to the same analog channel:
```python
analog_channel.digital_outputs = {
    "dig_out1": DigitalOutputChannel(opx_output=("con1", 1)),
    "dig_out2": DigitalOutputChannel(opx_output=("con1", 2)),
}
```
In this case, any digital pulses will be played to all digital channels.

### Digital-only channel
It is also possible to create a digital-only channel, i.e. using digital ports without any analog ports.
```python
from quam.components import Channel, DigitalOutputChannel
channel = Channel(
    id="channel",
    digital_outputs={"1": DigitalOutputChannel(opx_output=("con1", 1))},
)
```

## Digital pulses
Once a [DigitalOutputChannel][quam.components.channels.DigitalOutputChannel] is added to a [Channel][quam.components.channels.Channel], digital waveforms can be played on it. This is done by attaching a digital waveform to a [Pulse][quam.components.pulses.Pulse] through the attribute `Pulse.digital_marker`:

```python
from quam.components import pulses

pulse = pulses.SquarePulse(
    length=80,
    amplitude=0.2,
    digital_marker=[(1, 20), (0, 20), (1, 40)]
)
```
In the example above, the square pulse will also output digital waveform: "high" for 20 ns ⇨ "low" for 20 ns ⇨ "high" for 40 ns. This digital waveform will be played on all digital channels that are attached to the analog channel.

### Digital-only pulses
A digital pulse can also be played without a corresponding analog pulse.
This can be done by directly using the base [pulses.Pulse][quam.components.pulses.Pulse] class:
```python
channel.operations["digital"] = pulses.Pulse(length=100, digital_marker=[(1, 20, 0, 10)])
```