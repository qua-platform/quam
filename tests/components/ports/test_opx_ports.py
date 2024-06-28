import pytest
from quam.components.ports import (
    OPXPlusAnalogInputPort,
    OPXPlusAnalogOutputPort,
    OPXPlusDigitalOutputPort,
)


def test_opx_plus_analog_output_port():
    with pytest.raises(TypeError):
        OPXPlusAnalogOutputPort()

    port = OPXPlusAnalogOutputPort(port=("con1", 2))
    assert port.port == ("con1", 2)
    assert port.port_type == "analog_output"
    assert port.offset == 0.0
    assert port.delay == 0
    assert port.crosstalk == {}
    assert port.feedforward_filter == []
    assert port.feedback_filter == []
    assert port.shareable == False

    assert port.get_port_properties() == {
        "offset": 0.0,
        "delay": 0,
        "crosstalk": {},
        "feedforward_filter": [],
        "feedback_filter": [],
        "shareable": False,
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "analog_outputs": {
                    2: {
                        "offset": 0.0,
                        "delay": 0,
                        "crosstalk": {},
                        "feedforward_filter": [],
                        "feedback_filter": [],
                        "shareable": False,
                    }
                }
            }
        }
    }


def test_opx_plus_analog_input_port():
    with pytest.raises(TypeError):
        OPXPlusAnalogInputPort()

    port = OPXPlusAnalogInputPort(port=("con1", 2))
    assert port.port == ("con1", 2)
    assert port.port_type == "analog_input"
    assert port.offset == 0.0
    assert port.gain_db == 0
    assert port.shareable == False

    assert port.get_port_properties() == {
        "offset": 0.0,
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
                        "offset": 0.0,
                        "gain_db": 0,
                        "shareable": False,
                    }
                }
            }
        }
    }
