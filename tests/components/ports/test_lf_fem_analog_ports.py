import pytest

from quam.components.ports import LFFEMAnalogInputPort, LFFEMAnalogOutputPort


def test_lf_fem_analog_output_port():
    with pytest.raises(TypeError):
        LFFEMAnalogOutputPort()

    port = LFFEMAnalogOutputPort(port=("con1", 1, 2))
    assert port.port == ("con1", 1, 2)
    assert port.port_type == "analog_output"
    assert port.offset == 0.0
    assert port.delay == 0
    assert port.crosstalk == {}
    assert port.feedforward_filter == []
    assert port.feedback_filter == []
    assert port.shareable == False
    assert port.output_mode == "direct"
    assert port.sampling_rate == 1e9
    assert port.upsampling_mode == "mw"

    assert port.get_port_properties() == {
        "offset": 0.0,
        "delay": 0,
        "crosstalk": {},
        "feedforward_filter": [],
        "feedback_filter": [],
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
                        "analog_outputs": {
                            2: {
                                "offset": 0.0,
                                "delay": 0,
                                "crosstalk": {},
                                "feedforward_filter": [],
                                "feedback_filter": [],
                                "shareable": False,
                                "output_mode": "direct",
                                "sampling_rate": 1e9,
                                "upsampling_mode": "mw",
                            }
                        }
                    }
                }
            }
        }
    }


def test_lf_fem_analog_input_port():
    with pytest.raises(TypeError):
        LFFEMAnalogInputPort()

    port = LFFEMAnalogInputPort(port=("con1", 1, 2))
    assert port.port == ("con1", 1, 2)
    assert port.port_type == "analog_input"
    assert port.offset == 0.0
    assert port.gain_db == 0
    assert port.shareable == False
    assert port.sampling_rate == 1e9

    assert port.get_port_properties() == {
        "offset": 0.0,
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
                        "analog_inputs": {
                            2: {
                                "offset": 0.0,
                                "gain_db": 0,
                                "shareable": False,
                                "sampling_rate": 1e9,
                            }
                        }
                    }
                }
            }
        }
    }
