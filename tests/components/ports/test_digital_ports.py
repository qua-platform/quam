import pytest

from quam.components.ports import (
    FEMDigitalOutputPort,
    OPXPlusDigitalInputPort,
    OPXPlusDigitalOutputPort,
)


def test_opx_plus_digital_output_port():
    with pytest.raises(TypeError):
        OPXPlusDigitalOutputPort()

    port = OPXPlusDigitalOutputPort(port=("con1", 2))
    assert port.port == ("con1", 2)
    assert port.port_type == "digital_output"
    assert port.inverted == False
    assert port.shareable == False

    assert port.get_port_properties() == {
        "inverted": False,
        "shareable": False,
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "digital_outputs": {
                    2: {
                        "inverted": False,
                        "shareable": False,
                    }
                }
            }
        }
    }


def test_opx_plus_digital_input_port():
    with pytest.raises(TypeError):
        OPXPlusDigitalInputPort()

    port = OPXPlusDigitalInputPort(port=("con1", 2))
    assert port.port == ("con1", 2)
    assert port.port_type == "digital_input"
    assert port.deadtime == 4
    assert port.polarity == "rising"
    assert port.threshold == 2.0
    assert port.shareable == False

    assert port.get_port_properties() == {
        "deadtime": 4,
        "polarity": "rising",
        "threshold": 2.0,
        "shareable": False,
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "digital_inputs": {
                    2: {
                        "deadtime": 4,
                        "polarity": "rising",
                        "threshold": 2.0,
                        "shareable": False,
                    }
                }
            }
        }
    }


def test_fem_digital_output_port():
    with pytest.raises(TypeError):
        FEMDigitalOutputPort()

    port = FEMDigitalOutputPort(port=("con1", 1, 2))

    assert port.port == ("con1", 1, 2)
    assert port.port_type == "digital_output"
    assert port.inverted == False
    assert port.shareable == False
    assert port.level == "LVTTL"

    assert port.get_port_properties() == {
        "inverted": False,
        "shareable": False,
        "level": "LVTTL",
    }

    cfg = {"controllers": {}}
    port.apply_to_config(cfg)

    assert cfg == {
        "controllers": {
            "con1": {
                "fems": {
                    1: {
                        "digital_outputs": {
                            2: {
                                "inverted": False,
                                "shareable": False,
                                "level": "LVTTL",
                            }
                        }
                    }
                }
            }
        }
    }
