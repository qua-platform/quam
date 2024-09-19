import pytest

from quam.components.ports.analog_outputs import LFFEMAnalogOutputPort
from quam.components.ports.analog_inputs import LFFEMAnalogInputPort


def test_lf_fem_analog_output_port():
    with pytest.raises(TypeError):
        LFFEMAnalogOutputPort()

    port = LFFEMAnalogOutputPort("con1", 1, 2)
    assert port.controller_id == "con1"
    assert port.fem_id == 1
    assert port.port_id == 2
    assert port.port_tuple == ("con1", 1, 2)
    assert port.port_type == "analog_output"
    assert port.offset == None
    assert port.delay == 0
    assert port.crosstalk is None
    assert port.feedforward_filter is None
    assert port.feedback_filter is None
    assert port.shareable == False
    assert port.output_mode == "direct"
    assert port.sampling_rate == 1e9
    assert port.upsampling_mode == "mw"

    assert port.to_dict() == {
        "controller_id": "con1",
        "fem_id": 1,
        "port_id": 2,
    }

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "fems": {
                    1: {
                        "type": "LF",
                        "analog_outputs": {
                            2: {
                                "delay": 0,
                                "shareable": False,
                                "output_mode": "direct",
                                "sampling_rate": 1e9,
                                "upsampling_mode": "mw",
                            }
                        },
                    }
                }
            }
        }
    }

    port.offset = 0.1
    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "offset": 0.1,
    }

    port.sampling_rate = 2e9

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 2e9,
        "offset": 0.1,
    }


def test_lf_fem_analog_input_port():
    with pytest.raises(TypeError):
        LFFEMAnalogInputPort()

    port = LFFEMAnalogInputPort("con1", 1, 2)
    assert port.controller_id == "con1"
    assert port.fem_id == 1
    assert port.port_id == 2
    assert port.port_tuple == ("con1", 1, 2)

    assert port.port_type == "analog_input"
    assert port.offset is None
    assert port.gain_db == 0
    assert port.shareable == False
    assert port.sampling_rate == 1e9

    assert port.to_dict() == {
        "controller_id": "con1",
        "fem_id": 1,
        "port_id": 2,
    }

    assert port.get_port_properties() == {
        "gain_db": 0,
        "shareable": False,
        "sampling_rate": 1e9,
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "fems": {
                    1: {
                        "type": "LF",
                        "analog_inputs": {
                            2: {
                                "gain_db": 0,
                                "shareable": False,
                                "sampling_rate": 1e9,
                            }
                        },
                    }
                }
            }
        }
    }
