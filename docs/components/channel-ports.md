# Channel Ports

In the section [Channels](channels.md), we have seen how to create analog channels and attach digital outputs to them.
In these examples, the ports are defined by simple tuples like `(controller, fem, port)`.
However, for more advanced use cases and better organization, it is recommended to define ports using dedicated [Port][quam.components.ports.BasePort] QUAM components managed through port containers.
This approach provides several benefits:

1. **Centralized port management**: Define all ports in one location and reference them from channels.
2. **Port sharing**: Multiple channels can reference the same physical port with consistent properties.
3. **Advanced port properties**: Access hardware-specific features like crosstalk compensation, filters, sampling rates, and frequency conversion settings.

QUAM supports ports for three types of quantum control hardware:

- **LF-FEM Ports**: Low-frequency FEM modules using 3-element tuples `(controller_id, fem_id, port_id)` with support for high sampling rates and flexible output modes.
- **MW-FEM Ports**: Microwave FEM modules using 3-element tuples `(controller_id, fem_id, port_id)` with built-in frequency conversion, replacing the need for separate IQ channels with Octave frequency converters.
- **OPX+ Ports**: OPX+ controllers using 2-element tuples `(controller_id, port_id)` for simpler setups.

All port types are defined in the [quam.components.ports][quam.components.ports] module.

## Port Containers with BasicQuam

The recommended way to work with ports is to use a [FEMPortsContainer][quam.components.ports.FEMPortsContainer] attached to your [QuamRoot][quam.core.QuamRoot] object. This provides centralized port management and enables port references.

### Setting Up the Ports Container

Here's how to integrate a ports container into your QUAM state. For this example, we will be using [BasicFEMQuam][quam.components.BasicFEMQuam] to create the QUAM instance:

```python
from quam.components import BasicFEMQuam
from quam.components.ports import FEMPortsContainer

# Create a QUAM instance with ports container
machine = BasicFEMQuam(
    ports=FEMPortsContainer()
)

# Create ports using the container methods
machine.ports.get_analog_output(
    "con1", 1, 2,  # controller, fem_id, port_id
    create=True,
    offset=0.15,
    sampling_rate=2e9,  # 2 GHz sampling
)

machine.ports.get_mw_output(
    "con1", 1, 1,
    create=True,
    band=1,
    upconverter_frequency=5e9,  # 5 GHz upconverter
)
```

The `create=True` parameter automatically creates ports if they don't exist, simplifying setup code.

## Basic Port Usage

### LF-FEM Analog Output with Port References

For low-frequency control signals, use LF-FEM analog output ports referenced from your channels:

```python
from quam.components import BasicFEMQuam, SingleChannel
from quam.components.ports import FEMPortsContainer

# Create QUAM instance with ports
machine = BasicFEMQuam(ports=FEMPortsContainer())

# Create the port
port = machine.ports.get_analog_output(
    "con1", 1, 2,  # controller, fem_id, port_id
    create=True,
    offset=0.15,
    sampling_rate=2e9,
    output_mode="amplified",
)

# Create channel that references this port
machine.channels["drive"] = SingleChannel(
    opx_output=port.get_reference()  # Get reference from port
)
```

Notice that the channel uses `port.get_reference()` to get a string reference instead of passing the port object directly. This is the recommended pattern for port usage.

### MW-FEM for Microwave Control

For microwave applications, MW-FEM ports provide built-in frequency conversion, eliminating the need for separate IQ channels and external mixers:

```python
from quam.components import BasicFEMQuam
from quam.components.channels import MWChannel
from quam.components.ports import FEMPortsContainer

# Create QUAM instance with ports
machine = BasicFEMQuam(ports=FEMPortsContainer())

# Create MW-FEM output port for microwave drive
mw_port = machine.ports.get_mw_output(
    "con1", 1, 1,
    create=True,
    band=1,
    upconverter_frequency=5.5e9,  # 5.5 GHz LO frequency
    sampling_rate=1e9,
)

# Create MW channel with reference to MW-FEM port
machine.channels["qubit_xy"] = MWChannel(
    opx_output=mw_port.get_reference(),
    intermediate_frequency=100e6,  # 100 MHz IF
)
```

The MW-FEM port handles both I and Q components internally. Use [MWChannel][quam.components.channels.MWChannel] for output-only, [InMWChannel][quam.components.channels.InMWChannel] for input-only, or [InOutMWChannel][quam.components.channels.InOutMWChannel] for input+output applications.

### MW-FEM Readout with Linked Frequencies

For readout, link the downconverter frequency to the upconverter frequency:

```python
from quam.components.channels import InOutMWChannel

mw_output = machine.ports.get_mw_output("con1", 1, 1, create=True, band=1, upconverter_frequency=6e9)
mw_input = machine.ports.get_mw_input(
    "con1", 1, 1, create=True, band=1,
    downconverter_frequency=mw_output.get_reference("upconverter_frequency"),
)

machine.channels["readout"] = InOutMWChannel(
    opx_output=mw_output.get_reference(),
    opx_input=mw_input.get_reference(),
)
```

## Port Types and Hardware

### LF-FEM Ports

Low-frequency FEM ports support high sampling rates and various output modes:

```python
# LF-FEM analog output with advanced features
machine.ports.get_analog_output(
    "con1", 1, 2,  # controller, fem_id, port_id
    create=True,
    offset=0.15,
    sampling_rate=2e9,  # 1 GHz or 2 GHz
    output_mode="amplified",  # "direct" or "amplified"
    exponential_filter=[(10, 0.1), (20, 0.2)],  # For QOP >= 3.3.0
)
```

### MW-FEM Ports

Microwave FEM ports integrate frequency conversion for direct RF/microwave control:

```python
# MW-FEM output with upconverter
machine.ports.get_mw_output(
    "con1", 1, 1,  # controller, fem_id, port_id
    create=True,
    band=1,  # Required: 1 or 2
    upconverter_frequency=5.5e9,  # Upconversion LO frequency (Hz)
)
```

MW-FEM ports eliminate the need for external mixers and frequency converters.

## OPX+ Ports

For systems using OPX+ controllers, ports use a simpler 2-tuple addressing scheme.

### OPX+ Port Types

```python
# Analog output with filters
machine.ports.get_analog_output(
    "con1", 3,  # controller, port_id (note: only 2 elements)
    create=True,
    offset=0.2,
    feedforward_filter=[0.7, 0.2, 0.1],  # FIR filter
    feedback_filter=[0.3, 0.4, 0.5],  # IIR filter
)
```

### OPX+ with IQ Channels

When using OPX+ hardware, you may need IQ channels with separate I and Q ports:

```python
from quam.components import BasicOPXPlusQuam, IQChannel
from quam.components.ports import OPXPlusPortsContainer
from quam.components.hardware import FrequencyConverter, LocalOscillator, Mixer

# For OPX+ systems, use OPXPlusPortsContainer
machine = BasicOPXPlusQuam(ports=OPXPlusPortsContainer())

# Create I and Q ports
port_I = machine.ports.get_analog_output("con1", 1, create=True, offset=0.1)
port_Q = machine.ports.get_analog_output("con1", 2, create=True, offset=-0.05)

# Create IQ channel with port references
machine.channels["qubit_xy"] = IQChannel(
    opx_output_I=port_I.get_reference(),
    opx_output_Q=port_Q.get_reference(),
    intermediate_frequency=100e6,
    frequency_converter_up=FrequencyConverter(
        local_oscillator=LocalOscillator(frequency=6e9, power=10),
        mixer=Mixer(),
    )
)
```

Note: MW-FEM ports are preferred over this approach for microwave applications as they integrate frequency conversion.

## Port Container Methods

The [FEMPortsContainer][quam.components.ports.FEMPortsContainer] provides methods for each port type:

```python
# LF-FEM ports (3 parameters: controller, fem_id, port_id)
machine.ports.get_analog_output("con1", 1, 2, create=True)
machine.ports.get_analog_input("con1", 1, 1, create=True)
machine.ports.get_digital_output("con1", 1, 1, create=True)

# MW-FEM ports
machine.ports.get_mw_output("con1", 1, 1, create=True, band=1, upconverter_frequency=5e9)
machine.ports.get_mw_input("con1", 1, 1, create=True, band=1, downconverter_frequency=5e9)
```

For [OPXPlusPortsContainer][quam.components.ports.OPXPlusPortsContainer], use 2 parameters (controller, port_id):

```python
machine.ports.get_analog_output("con1", 3, create=True)
machine.ports.get_digital_input("con1", 1, create=True)
```

## Port References

Use `port.get_reference()` to get string references for ports. See basic examples in [Basic Port Usage](#basic-port-usage) above.

To reference specific attributes, use `port.get_reference("attribute_name")`. This is useful for linking converter frequencies:

```python
mw_output = machine.ports.get_mw_output("con1", 1, 1, create=True, upconverter_frequency=5e9)
mw_input = machine.ports.get_mw_input(
    "con1", 1, 1, create=True,
    downconverter_frequency=mw_output.get_reference("upconverter_frequency"),
)
```

## Advanced Features

Ports support crosstalk compensation, FIR/IIR filters (OPX+), and exponential filters (LF-FEM). Refer to the [API documentation][quam.components.ports] for complete parameter details.

## Best Practices

- **Use port references**: Always use `port.get_reference()` instead of passing port objects directly
- **Centralized management**: Create all ports before channels for better organization
- **Use port properties**: Directly set port properties on the port object rather than through channel attributes, as they are deprecated.
- **Port sharing**: Set `shareable=True` when multiple channels use the same port
- **Choose the right type**: MW-FEM for microwave/RF, LF-FEM for high-rate baseband/IF
