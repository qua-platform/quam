# Channels

In the QuAM library, channels are a fundamental concept that represent the physical connections to the quantum hardware. They are defined in the [quam.components.channels][quam.components.channels] module.

We distinguish between the following channel types, where the terms "output" and "input" are always from the perspective of the OPX hardware:

**1. Analog output channels**

- [SingleChannel][quam.components.channels.SingleChannel]: Represents a single OPX output channel.
- [IQChannel][quam.components.IQChannel]: Represents an IQ OPX output channel.

**2. Analog output + input channels**

- [InOutSingleChannel][quam.components.channels.InOutSingleChannel]: Represents a single OPX output + input channel.
- [InOutIQChannel][quam.components.channels.InOutIQChannel]: Represents an IQ OPX output + input channel.

**3. Digital channels**  

- [DigitalOutputChannel][quam.components.channels.DigitalOutputChannel]: Represents a digital output channel.

Each analog [Channel][quam.components.channels.Channel] corresponds to an element in QUA, whereas the digital channel is part of an analog channel.

These channel combinations cover most use cases, although there are exceptions (input-only channels and single-output, IQ-input channels) which will be implemented in a subsequent QuAM release. If you need such channels, please create a [Github issue](https://github.com/qua-platform/quam/issues).


## Analog Output Channels

Analog output channels are the primary means of controlling the quantum hardware. They can be used to send various types of signals, such as microwave or RF signals, to control the quantum system. The two types of analog output channels are the [SingleChannel][quam.components.channels.SingleChannel] and the [IQChannel][quam.components.channels.IQChannel]. 


### Analog Channel Ports

A [SingleChannel][quam.components.channels.SingleChannel] is always attached to a single OPX output port, and similarly an [IQChannel][quam.components.channels.IQChannel] has an associated pair of IQ ports:

```python
from quam.components import SingleChannel, IQChannel

single_channel = SingleChannel(
    opx_output=("con1", 1),
    ...
)
IQ_channel = IQChannel(
    opx_output_I=("con1", 2),
    opx_output_Q=("con1", 3),
    ...
)
```


### DC Offset
Each analog channel can have a specified DC offset that remains for the duration of the QUA program.
This can be set through `SingleChannel.opx_output_offset` for the [SingleChannel][quam.components.channels.SingleChannel], and through `IQChannel.opx_output_offset_I` and `IQChannel.opx_output_offset_Q` for the [IQChannel][quam.components.channels.IQChannel].

Note that if multiple channels are attached to the same OPX output port(s), they may not have different output offsets.
This raises a warning and chooses the DC offset of the last channel. 

The DC offset can also be modified while a QUA program is running:
```python
from qm.qua import program

with program() as prog:
    single_channel.set_dc_offset(offset=0.1)
    IQ_channel.set_dc_offset(offset=0.25, element_input="I")  # Set offset of port I
```
The offsets can also be QUA variables.
[Channel.set_dc_offset()][quam.components.channels.SingleChannel.set_dc_offset] is a light wrapper around `qm.qua.set_dc_offset` to attach it to the channel.


### Frequency Converters
The `IQChannel` is usually connected to a mixer to upconvert the signal using a local oscillator.
This frequency upconversion is represented in QuAM by a [FrequencyConverter][quam.components.hardware.FrequencyConverter]

```python
from quam.components.hardware import FrequencyConverter, LocalOscillator, Mixer

IQ_channel = IQChannel(
    opx_output_I=("con1", 2),
    opx_output_Q=("con1", 3),
    intermediate_frequency=100e6,  # Hz
    frequency_converter=FrequencyConverter(
        local_oscillator=LocalOscillator(frequency=6e9, power=10),
        mixer=Mixer(),
    )
)
```

Integrated frequency conversion systems such as [QM's Octave](https://docs.quantum-machines.co/1.1.7/qm-qua-sdk/docs/Hardware/octave/) usually have additional features such as auto-calibration.
For this reason they have a specialized frequency converter such as the [OctaveUpConverter][quam.components.octave.OctaveUpConverter].
See the [QuAM Octave Documentation][octave] documentation for details.


### Analog Pulses
QuAM has a range of standard [Pulse][quam.components.pulses.Pulse] components in [quam.components.pulses][quam.components.pulses].
These pulses can be registered as part of the analog channel via `Channel.operations` such that the channel can output the associated pulse waveforms:

```python
from quam.components import pulses

channel.operations["X180"] = pulses.SquarePulse(
    amplitude=0.1,  # V
    length=16,  # ns
)
```

Once a pulse has been registered in a channel, it can be played within a QUA program:

```python
with program() as prog:
    channel.play("X180")
```
[Channel.play()][quam.components.channels.Channel.play] is a light wrapper around [qm.qua.play()](https://docs.quantum-machines.co/latest/qm-qua-sdk/docs/Introduction/qua_overview/?h=play#play-statement) to attach it to the channel.

Details on pulses in QuAM can be found at the [Pulses Documentation][pulses].

## Analog Output + Input Channels
Aside from sending signals to the quantum hardware, data is usually also received back, and subsequently read out through the hardware's input ports.
In QuAM, this is represented using the [InOutSingleChannel][quam.components.channels.InOutSingleChannel] and the [InOutIQChannel][quam.components.channels.InOutIQChannel].
These channels don't only have associated output port(s) but also input port(s):

```python
from quam.components import InOutSingleChannel, InOutIQChannel

single_io_channel = InOutSingleChannel(
    opx_output=("con1", 1),
    opx_input=("con1", 1)
    ...
)
IQ_io_channel = InOutIQChannel(
    opx_output_I=("con1", 2),
    opx_output_Q=("con1", 3),
    opx_input_I=("con1", 1),
    opx_input_Q=("con1", 2)
    ...
)
```

These are extensions of the [SingleChannel][quam.components.channels.SingleChannel] and the [IQChannel][quam.components.channels.IQChannel] that add relevant features for readout.

Both the [InOutSingleChannel][quam.components.channels.InOutSingleChannel] and the [InOutIQChannel][quam.components.channels.InOutIQChannel] combine output + input as in most cases a signal is also sent to probe the quantum hardware.
Support for input-only analog channels is planned for a future release.


### Readout Pulses
Channels that have input ports can also have readout pulses:

```python
from quam.components import pulses
io_channel.operations["readout"] = pulses.SquareReadoutPulse(
    length=16,  # ns
    amplitude=0.1,  # V
    integration_weights_angle=0.0,  # rad, optional rotation of readout signal
)
```
As can be seen, the readout pulse (in this case [SquareReadoutPulse][quam.components.pulses.SquareReadoutPulse]) is similar to the regular pulses, but with additional parameters for readout.
Specifically, it contains the attributes `integration_weights_angle` and `integration_weights` to specify how the readout signal should be integrated.


## Digital Channels
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


### Digital-only Channel
It is also possible to create a digital-only channel, i.e. using digital ports without any analog ports.
```python
from quam.components import Channel, DigitalOutputChannel
channel = Channel(
    id="channel",
    digital_outputs={"1": DigitalOutputChannel(opx_output=("con1", 1))},
)
```


## Digital Pulses
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


### Digital-only Pulses
A digital pulse can also be played without a corresponding analog pulse.
This can be done by directly using the base [pulses.Pulse][quam.components.pulses.Pulse] class:
```python
channel.operations["digital"] = pulses.Pulse(length=100, digital_marker=[(1, 20, 0, 10)])
```

## Sticky channels
A channel can be set to be sticky, meaning that the voltage after a pulse will remain at the last value of the pulse.
Details can be found in the [Sticky channel QUA documentation](https://docs.quantum-machines.co/latest/docs/Guides/features/#sticky-element).
Any channel can be made sticky by adding the [channels.StickyChannelAddon][quam.components.channels.StickyChannelAddon] to it:
```python
from quam.components.channels import StickyChannelAddon

channel.sticky = StickyChannelAddon(duration=...)
```