# Channel Ports

In the section [Channels](channels.md), we have seen how to create analog channels and attach digital outputs to them. 
In these examples, the ports are defined by the OPX output tuple `(connector, port)`.
However, for more advanced use cases it is instead possible to define the ports using dedicated [Port][quam.components.ports.Port] QuAM components.
This is primarily useful in two situations:

1. Multiple channels are connected to the same physical port, and the user wants to define the port and its properties only once.
2. The user wants to access port-specific properties that cannot directly be accessed through the [Channel][quam.components.channels.Channel]. Examples are the crosstalk, delay, and sampling rate of the port.

## Example: Defining a Port
In this example, we want to use analog output ("con1", 3) of the OPX+ to create a single channel.
We define the port using the [OPXPlusAnalogOutputPort][quam.components.ports.OPXPlusAnalogOutputPort] component, which allows us to set the offset and delay of the port.
 
```python
from quam.components.ports import OPXPlusAnalogOutputPort
from quam.components import SingleChannel

port = OPXPlusAnalogOutputPort(port=("con1", 3), offset=0.2, delay=12)
channel = SingleChannel(opx_output=port)
```

Note that in this situation the port offset is defined by `channel.port.offset`, and is therefore part of the port.
The [SingleChannel][quam.components.channels.SingleChannel] component also has the attribute `SingleChannel.OPX_output_offset`, but its value is ignored in this case.
If we would have instead used `SingleChannel.opx_output = ("con1", 3)`, then the offset would have been defined by `channel.OPX_output_offset`.