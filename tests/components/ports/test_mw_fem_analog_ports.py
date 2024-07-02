import pytest

from quam.components.ports.analog_outputs import MWFEMAnalogOutputPort
from quam.components.ports.analog_inputs import MWFEMAnalogInputPort


def test_mw_fem_analog_output_port():
    with pytest.raises(TypeError):
        MWFEMAnalogOutputPort()

    with pytest.raises(TypeError):
        port = MWFEMAnalogOutputPort("con1", 1, 2)

    with pytest.raises(ValueError):
        port = MWFEMAnalogOutputPort("con1", 1, 2, band=1)

    port = MWFEMAnalogOutputPort("con1", 1, 2, band=1, upconverter_frequency=5e9)
    assert port.controller_id == "con1"
    assert port.fem_id == 1
    assert port.port_id == 2
    assert port.port_tuple == ("con1", 1, 2)
    assert port.port_type == "analog_output"
    assert port.band == 1
    assert port.upconverter_frequency == 5e9
    assert port.upconverters is None
    assert port.delay == 0
    assert port.shareable == False
    assert port.sampling_rate == 1e9
    assert port.full_scale_power_dbm == -11

    assert port.to_dict() == {
        "controller_id": "con1",
        "fem_id": 1,
        "port_id": 2,
        "band": 1,
        "upconverter_frequency": 5e9,
    }

    assert port.get_port_properties() == {
        "band": 1,
        "delay": 0,
        "shareable": False,
        "sampling_rate": 1e9,
        "full_scale_power_dbm": -11,
        "upconverter_frequency": 5e9,
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "fems": {
                    1: {
                        "type": "MW",
                        "analog_outputs": {
                            2: {
                                "band": 1,
                                "upconverter_frequency": 5e9,
                                "delay": 0,
                                "shareable": False,
                                "sampling_rate": 1e9,
                                "full_scale_power_dbm": -11,
                            }
                        }
                    }
                }
            }
        }
    }


def test_mw_fem_analog_input_ports():
    with pytest.raises(TypeError):
        MWFEMAnalogInputPort()

    with pytest.raises(TypeError):
        port = MWFEMAnalogInputPort("con1", 1, 2)

    port = MWFEMAnalogInputPort("con1", 1, 2, band=1, downconverter_frequency=5e9)

    assert port.controller_id == "con1"
    assert port.fem_id == 1
    assert port.port_id == 2
    assert port.port_tuple == ("con1", 1, 2)
    assert port.port_type == "analog_input"
    assert port.band == 1
    assert port.downconverter_frequency == 5e9
    assert port.sampling_rate == 1e9
    assert port.shareable == False

    assert port.to_dict() == {
        "controller_id": "con1",
        "fem_id": 1,
        "port_id": 2,
        "band": 1,
        "downconverter_frequency": 5e9,
    }

    assert port.get_port_properties() == {
        "band": 1,
        "downconverter_frequency": 5e9,
        "sampling_rate": 1e9,
        "shareable": False,
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "fems": {
                    1: {
                        "type": "MW",
                        "analog_inputs": {
                            2: {
                                "band": 1,
                                "downconverter_frequency": 5e9,
                                "sampling_rate": 1e9,
                                "shareable": False,
                            }
                        }
                    }
                }
            }
        }
    }
