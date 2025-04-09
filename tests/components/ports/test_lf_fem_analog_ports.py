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
        "__class__": "quam.components.ports.analog_outputs.LFFEMAnalogOutputPort",
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


def test_fem_analog_output_port_filter():
    port = LFFEMAnalogOutputPort("con1", 1, 2)
    port.feedforward_filter = None
    port.feedback_filter = None

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
    }

    port.feedforward_filter = [0.7, 0.2, 0.1]

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"feedforward": [0.7, 0.2, 0.1]},
    }

    port.feedback_filter = [0.3, 0.4, 0.5]

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"feedforward": [0.7, 0.2, 0.1], "feedback": [0.3, 0.4, 0.5]},
    }

    port.feedforward_filter = None
    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"feedback": [0.3, 0.4, 0.5]},
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
        "__class__": "quam.components.ports.analog_inputs.LFFEMAnalogInputPort",
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


def test_lf_fem_analog_output_port_exponential_filter():
    port = LFFEMAnalogOutputPort("con1", 1, 2)
    port.exponential_filter = [(10, 0.1), (20, 0.2)]
    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"exponential": [(10, 0.1), (20, 0.2)]},
    }

    # Add feedforward filter alongside exponential filter
    port.feedforward_filter = [0.7, 0.2, 0.1]
    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {
            "exponential": [(10, 0.1), (20, 0.2)],
            "feedforward": [0.7, 0.2, 0.1],
        },
    }

    # Adding feedback filter should raise ValueError due to QOP version compatibility
    port.feedback_filter = [0.3, 0.4, 0.5]
    with pytest.raises(ValueError, match="Please only specify 'exponential_filter' "):
        port.get_port_properties()
    # Remove exponential filter and verify feedback filter works
    port.exponential_filter = None
    port.feedback_filter = [0.3, 0.4, 0.5]
    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "output_mode": "direct",
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"feedforward": [0.7, 0.2, 0.1], "feedback": [0.3, 0.4, 0.5]},
    }
