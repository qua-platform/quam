# Pulses
In the QuAM framework, pulses are the fundamental building blocks for crafting signals that interact with quantum processors.
These parametrized representations of waveforms, emitted from the OPX analog outputs, allow precise control over the shape and timing of signals.
For instance, a square pulse, defined by its amplitude and duration, can be used to initialize a quantum state or implement a gate operation.
This section explains how pulses are used in QuAM to facilitate quantum computing experiments.

All pulses in QuAM are instances of the [Pulse][quam.components.pulses.Pulse] class. The QuAM library includes several predefined pulse types, such as:

- **[SquarePulse][quam.components.pulses.SquarePulse]**: Typically used for simple quantum operations like flips or resets, characterized by a constant amplitude throughout its duration.
- **[GaussianPulse][quam.components.pulses.GaussianPulse]**: Ideal for minimizing spectral leakage due to its smooth rise and fall, commonly used in operations requiring high fidelity.
- **[DragPulse][quam.components.pulses.DragPulse]**: Designed to correct phase errors in quantum gates, enhancing the accuracy of operations involving superconducting qubits.

The full list of predefined pulses can be found in the [pulses][quam.components.pulses] module.
Users can also define custom pulses by subclassing the `Pulse` class. This flexibility allows the creation of tailored waveforms that suit specific experimental requirements.

All pulses in QuAM are instances of the [Pulse][quam.components.pulses.Pulse] class.
The QuAM library contains a set of common pulse types in the [pulses][quam.components.pulses] module.
Typical examples are [SquarePulse][quam.components.pulses.SquarePulse], [GaussianPulse][quam.components.pulses.GaussianPulse], and [DragPulse][quam.components.pulses.DragPulse].
Users can supplement these common pulses with their own custom pulses by subclassing the [Pulse][quam.components.pulses.Pulse] class (see [Custom QuAM components][custom-components] for details). 
<!-- TODO Fix reference -->

<!-- /// details | Pulses in QuAM versus the QUA configuration
    type: tip
    open: True

QuAM and QUA handle pulses differently. QUA decomposes pulses into "waveforms", "integration_weights", etc., each referenced by name in the "pulses" section. An element's pulse_mapping links a label (e.g., "X180") to a specific pulse. This allows multiple pulses to share a waveform and vice versa, but it scatters pulse information across sections, complicating modifications. It also often requires external functions to populate waveforms due to the absence of a parametrized representation.

On the other hand, QuAM uses a parametrized class to represent pulses. A pulse's type and parameters (length, amplitude, etc.) define it, and these parameters generate the waveform via [Pulse.generate_waveform()][quam.components.pulses.Pulse.generate_waveform]. The resulting pulse mapping, waveform, and optional integration weights are then added to the QUA configuration.
/// -->


## Usage
To implement pulses in a QuAM program, you first need to register them to a specific channel. Here's how to set up a channel and register a square pulse for an operation labeled "X180":

```python
from quam.components import pulses, SingleChannel

# Create a channel associated with the first output on connector 1
channel = SingleChannel(opx_output=("con1", 1))

# Register a square pulse with a duration of 1000 units and amplitude of 0.5
channel.operations["X180"] = pulses.SquarePulse(duration=1000, amplitude=0.5)```
```

After registering a pulse, you can utilize it in a QuAM program. Below is a simple example where the "X180" pulse is played:

```python
from qm.qua import program

# Start a new QuAM program
with program() as prog:
    # Play the "X180" pulse on the previously defined channel
    channel.play("X180")
```


## Comparing QuAM and QUA Configurations

The handling of pulses in QuAM and QUA presents fundamental differences in design philosophy and implementation, which can impact both usability and functionality. Understanding these differences is key for users who are transitioning to QuAM. Here's a comparison of how pulses are configured in each system:

### QUA Configuration

In the QUA configuration, pulses are decomposed into multiple components, such as `"waveforms"` and `"integration_weights"`. These components are defined separately and referenced by name within the "pulses" section of the configuration:

- **Decomposition**: Each pulse is linked to a specific waveform and optionally, integration weights. This modular approach can be flexible but may lead to fragmented configuration, where information about a single pulse is scattered across multiple sections.
- **Pulse Mapping**: The elements (channels) use a `pulse_mapping` to link a label (e.g., "X180") to  a specific pulse setup. This system allows multiple channels to share a pulse, enhancing reusability but potentially complicating pulse modifications.
- **External Functions**: Typically, the lack of a parametrized representation means that external functions are often required to populate waveform parameters, which can add complexity to pulse configuration and maintenance.

### QuAM Configuration

Conversely, QuAM adopts a parametrized approach that encapsulates all pulse characteristics within a single class, aiming to simplify pulse definition and manipulation:

- **Parametrized Representation**: Pulses in QuAM are instances of a parametrized class, where the type of pulse and its parameters (such as length and amplitude) are directly defined by the user. This simplifies the initial setup and modification of pulse configurations.
- **Waveform Generation**: These parameters are used to generate the waveform dynamically using the method `[Pulse.generate_waveform()][quam.components.pulses.Pulse.generate_waveform]`. This approach integrates waveform generation within the pulse definition, streamlining the configuration process.
- **Integrated Configuration**: The resulting pulse definition includes not only the waveform but also the mapping and any optional integration weights, all encapsulated within a single entity. This integration simplifies the management and updating of pulses within the QuAM system.
- **No built-in waveform reuse**: QuAM does not currently support sharing waveforms across pulses, as each pulse is defined independently. This can have implications for memory usage on the OPX. Reusing waveforms in QuAM is planned in a future release.

### Conclusion

Understanding the relationship between QuAM and QUA helps users navigate the choices available to them, balancing ease of use with the power and flexibility offered by direct QUA scripting. 
By considering these aspects, users can better choose or adapt their system according to their specific needs and technical preferences.