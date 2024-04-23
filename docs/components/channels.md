# Channels

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