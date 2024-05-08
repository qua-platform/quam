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
Users can supplement these common pulses with their own custom pulses by subclassing the [Pulse][quam.components.pulses.Pulse] class (see [Custom QuAM Components](/components/custom-components) for details). 


## Usage
To implement pulses in a QuAM program, you first need to register them to a specific channel. Here's how to set up a channel and register a square pulse for an operation labeled `"X180"`:

```python
from quam.components import pulses, SingleChannel

# Create a channel associated with the first output on connector 1
channel = SingleChannel(opx_output=("con1", 1))

# Register a square pulse with a duration of 1000 units and amplitude of 0.5
channel.operations["X180"] = pulses.SquarePulse(duration=1000, amplitude=0.5)
```

After registering a pulse, you can utilize it in a QuAM program. Below is a simple example where the `"X180"` pulse is played:

```python
from qm.qua import program

# Start a new QuAM program
with program() as prog:
    # Play the "X180" pulse on the previously defined channel
    channel.play("X180")
```

## Readout Pulses
In addition to control pulses, QuAM also supports readout pulses, which are used to measure the state of a quantum system.
These pulses should be attached to an input channel, either [InOutIQChannel][quam.components.channels.InOutIQChannel] or [InOutSingleChannel][quam.components.channels.InOutSingleChannel].

Here's an example of how to define a readout pulse for a channel:

```python
readout_channel.operations["readout"] = pulses.SquareReadoutPulse(
    length=1000, 
    amplitude=0.1
    integration_weights=[(1, 500)]    
)
```

Once a readout pulse is defined, it can be used in a QuAM program to measure the state of the quantum system:

```python
with program() as prog:
    # Measure the state of the quantum system using the "readout" pulse
    qua_result = readout_channel.measure("readout")
```

## Creating Custom Pulses
To create custom pulses in QuAM, you can extend the functionality of the Pulse class by subclassing it and defining your own waveform generation logic. This allows for precise control over the pulse characteristics.

### Example: Creating a Ramp Pulse
To illustrate, let's create a pulse that ramps in amplitude. This involves subclassing the Pulse class from the QuAM library and defining specific parameters and the waveform function.

```python
import numpy as np
from quam.core import quam_dataclass
from quam.components import pulses

@quam_dataclass
class RampPulse(pulses.Pulse):
    # Define the starting and stopping amplitudes for the ramp pulse
    amplitude_start: float
    amplitude_stop: float

    def waveform_function(self) -> np.ndarray:
        # This function generates a linearly spaced array to form a ramp waveform
        return np.linspace(self.amplitude_start, self.amplitude_stop, self.length)
```
Ensure this code is saved in a properly structured Python module within your project so that it can be imported as needed. For details on organizing custom components, refer to the [Custom QuAM Components](/components/custom-components) section of the QuAM documentation

### Extending to Readout Pulses
To create a readout pulse derived from a control pulse, subclass both the specific control pulse and the [ReadoutPulse][quam.components.pulses.ReadoutPulse] class. Below is an example of how to adapt the RampPulse into a readout pulse.

```python
@quam_dataclass
class RampReadoutPulse(pulses.ReadoutPulse, RampPulse):
    """Extend RampPulse to include readout-specific functionality."""
    # No additional fields needed; inherits all from RampPulse and ReadoutPulse
    pass
```
Readout pulses utilize additional parameters for integration weights which are crucial for signal processing:

- **`ReadoutPulse.integration_weights`**: A list of floats or tuples specifying the weights over time.
- **`ReadoutPulse.integration_weights_angle`**: The angle (in radians) applied to the integration weights.

These two parameters are used to calculate the readout pulse's integration weights (`sine`, `-sine` and `cosine`), which are essential for signal processing in readout operations.

These parameters are typically used to manage the integration weights (`sine`, `-sine`, and `cosine`) for the readout operations. By default, these weights assume a fixed angle. If variable angles are needed, subclass the [BaseReadoutPulse][quam.components.pulses.BaseReadoutPulse] class and override the `integration_weights_function()` to customize this behavior.

This approach ensures your custom pulse configurations are both flexible and compatible with the broader QuAM framework.


## Pulses in QuAM and QUA

The handling of pulses in QuAM and QUA presents fundamental differences in design philosophy and implementation, which can impact both usability and functionality. Understanding these differences is key for users who are transitioning to QuAM. Here's a comparison of how pulses are configured in each system:

### QUA Configuration

In the QUA configuration, pulses are decomposed into multiple components, such as `"waveforms"` and `"integration_weights"`. These components are defined separately and referenced by name within the `"pulses"` section of the configuration:

- **Decomposition**: Each pulse is linked to a specific waveform and optionally, integration weights. This modular approach is more memory-efficient but may lead to fragmented configuration, where information about a single pulse is scattered across multiple sections.
- **Pulse Mapping**: The elements (channels) use an `operations` mapping to link a label (e.g., "X180") to  a specific pulse setup. This system allows multiple channels to share a pulse, enhancing reusability but potentially complicating pulse modifications.
- **External Functions**: Typically, the lack of a parametrized representation means that external functions are often required to populate waveform entries.

### QuAM Configuration

Conversely, QuAM adopts a parametrized approach that encapsulates all pulse characteristics within a single class, aiming to simplify pulse definition and manipulation:

- **Parametrized Representation**: Pulses in QuAM are instances of a parametrized class, where the type of pulse and its parameters (such as length and amplitude) are directly defined by the user. This simplifies the initial setup and modification of pulse configurations.
- **Waveform Generation**: These parameters are used to generate the waveform dynamically using the method `waveform_function()`. This approach integrates waveform generation within the pulse definition, streamlining the configuration process.
- **No built-in waveform reuse**: QuAM does not currently support sharing waveforms across pulses, as each pulse is defined independently. This can have implications for memory usage on the OPX. Reusing waveforms in QuAM is planned in a future release.

### Conclusion

Understanding the relationship between QuAM and QUA helps users navigate the choices available to them, balancing ease of use with the power and flexibility offered by direct QUA scripting. 
By considering these aspects, users can better choose or adapt their system according to their specific needs and technical preferences.