import pytest
from quam.components.ports.analog_inputs import OPXPlusAnalogInputPort
from quam.components.ports.analog_outputs import OPXPlusAnalogOutputPort


def test_opx_plus_analog_output_port():
    with pytest.raises(TypeError):
        OPXPlusAnalogOutputPort()

    port = OPXPlusAnalogOutputPort("con1", 2)
    assert port.controller_id == "con1"
    assert port.port_id == 2
    assert port.port_tuple == ("con1", 2)
    assert port.port_type == "analog_output"
    assert port.offset is None
    assert port.delay == 0
    assert port.crosstalk is None
    assert port.feedforward_filter is None
    assert port.feedback_filter is None
    assert port.shareable == False

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
    }

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "analog_outputs": {
                    2: {
                        "delay": 0,
                        "shareable": False,
                    }
                }
            }
        }
    }


def test_opx_plus_analog_input_port():
    with pytest.raises(TypeError):
        OPXPlusAnalogInputPort()

    port = OPXPlusAnalogInputPort("con1", 2)
    assert port.controller_id == "con1"
    assert port.port_id == 2
    assert port.port_tuple == ("con1", 2)
    assert port.port_type == "analog_input"
    assert port.offset is None
    assert port.gain_db == 0
    assert port.shareable == False

    assert port.get_port_properties() == {
        "gain_db": 0,
        "shareable": False,
    }

    assert port.get_port_properties() == {
        "gain_db": 0,
        "shareable": False,
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "analog_inputs": {
                    2: {
                        "gain_db": 0,
                        "shareable": False,
                    }
                }
            }
        }
    }
