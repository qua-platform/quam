import pytest
from quam.components.ports import (
    OPXPlusPortsContainer,
    FEMPortsContainer,
    OPXPlusAnalogOutputPort,
    LFFEMAnalogOutputPort,
)
from quam.components.ports.analog_inputs import (
    LFFEMAnalogInputPort,
    MWFEMAnalogInputPort,
    OPXPlusAnalogInputPort,
)
from quam.components.ports.analog_outputs import MWFEMAnalogOutputPort
from quam.components.ports.digital_inputs import OPXPlusDigitalInputPort
from quam.components.ports.digital_outputs import (
    FEMDigitalOutputPort,
    OPXPlusDigitalOutputPort,
)


def test_opx_plus_ports_container_initialize():
    ports_container = OPXPlusPortsContainer()
    assert ports_container.analog_outputs == {}
    assert ports_container.analog_inputs == {}
    assert ports_container.digital_outputs == {}
    assert ports_container.digital_inputs == {}


def test_fem_ports_container_initialize():
    ports_container = FEMPortsContainer()
    assert ports_container.analog_outputs == {}
    assert ports_container.analog_inputs == {}
    assert ports_container.mw_outputs == {}
    assert ports_container.mw_inputs == {}
    assert ports_container.digital_outputs == {}


@pytest.mark.parametrize(
    "port_type", ["analog_output", "analog_input", "digital_output", "digital_input"]
)
def test_opx_plus_ports_container_add_ports(port_type):
    port_mapping = {
        "analog_output": OPXPlusAnalogOutputPort,
        "analog_input": OPXPlusAnalogInputPort,
        "digital_output": OPXPlusDigitalOutputPort,
        "digital_input": OPXPlusDigitalInputPort,
    }

    ports_container = OPXPlusPortsContainer()

    get_port_func = getattr(ports_container, f"get_{port_type}")

    with pytest.raises(KeyError):
        get_port_func("con1", 2)

    port = get_port_func("con2", 3, create=True)
    assert isinstance(port, port_mapping[port_type])

    assert port.controller_id == "con2"
    assert port.port_id == 3

    port2 = get_port_func("con2", 3, create=False)
    assert port is port2

    port3 = get_port_func("con2", 3, create=True)
    assert port is port3

    ports_group = getattr(ports_container, f"{port_type}s")
    assert port is ports_group["con2"][3]


@pytest.mark.parametrize(
    "port_type", ["analog_output", "analog_input", "digital_output", "digital_input"]
)
def test_opx_plus_ports_container_reference_to_port(port_type):
    port_mapping = {
        "analog_output": OPXPlusAnalogOutputPort,
        "analog_input": OPXPlusAnalogInputPort,
        "digital_output": OPXPlusDigitalOutputPort,
        "digital_input": OPXPlusDigitalInputPort,
    }

    ports_container = OPXPlusPortsContainer()

    port_reference = f"#/{port_type}s/con1/3"

    with pytest.raises(KeyError):
        ports_container.reference_to_port(port_reference)

    port = ports_container.reference_to_port(port_reference, create=True)
    assert isinstance(port, port_mapping[port_type])

    assert port.controller_id == "con1"
    assert port.port_id == 3

    port2 = ports_container.reference_to_port(port_reference, create=False)
    assert port is port2

    port3 = ports_container.reference_to_port(port_reference, create=True)
    assert port is port3

    ports_group = getattr(ports_container, f"{port_type}s")
    assert port is ports_group["con1"][3]


@pytest.mark.parametrize(
    "port_type",
    ["analog_output", "analog_input", "mw_output", "mw_input", "digital_output"],
)
def test_fem_ports_container_add_ports(port_type):
    port_mapping = {
        "analog_output": LFFEMAnalogOutputPort,
        "analog_input": LFFEMAnalogInputPort,
        "mw_output": MWFEMAnalogOutputPort,
        "mw_input": MWFEMAnalogInputPort,
        "digital_output": FEMDigitalOutputPort,
    }

    ports_container = FEMPortsContainer()

    get_port_func = getattr(ports_container, f"get_{port_type}")

    with pytest.raises(KeyError):
        get_port_func("con1", 1, 2)

    port = get_port_func("con2", 2, 3, create=True)
    assert isinstance(port, port_mapping[port_type])

    assert port.controller_id == "con2"
    assert port.fem_id == 2
    assert port.port_id == 3

    port2 = get_port_func("con2", 2, 3, create=False)
    assert port is port2

    port3 = get_port_func("con2", 2, 3, create=True)
    assert port is port3

    ports_group = getattr(ports_container, f"{port_type}s")
    assert port is ports_group["con2"][2][3]


@pytest.mark.parametrize(
    "port_type",
    ["analog_output", "analog_input", "mw_output", "mw_input", "digital_output"],
)
def test_fem_ports_container_reference_to_port(port_type):
    port_mapping = {
        "analog_output": LFFEMAnalogOutputPort,
        "analog_input": LFFEMAnalogInputPort,
        "mw_output": MWFEMAnalogOutputPort,
        "mw_input": MWFEMAnalogInputPort,
        "digital_output": FEMDigitalOutputPort,
    }

    port_reference = f"#/{port_type}s/con1/2/3"

    ports_container = FEMPortsContainer()

    with pytest.raises(KeyError):
        ports_container.reference_to_port(port_reference)

    port = ports_container.reference_to_port(port_reference, create=True)
    assert isinstance(port, port_mapping[port_type])

    assert port.controller_id == "con1"
    assert port.fem_id == 2
    assert port.port_id == 3

    port2 = ports_container.reference_to_port(port_reference, create=False)
    assert port is port2

    port3 = ports_container.reference_to_port(port_reference, create=True)
    assert port is port3

    ports_group = getattr(ports_container, f"{port_type}s")
    assert port is ports_group["con1"][2][3]
