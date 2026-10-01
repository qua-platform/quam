import pytest

from quam.components.ports.analog_outputs import BBFEMAnalogOutputPort
from quam.components.ports.analog_inputs import BBFEMAnalogInputPort


def test_bb_fem_analog_output_port():
    with pytest.raises(TypeError):
        BBFEMAnalogOutputPort()

    port = BBFEMAnalogOutputPort("con1", 1, 2)
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
    assert port.sampling_rate == 1e9
    assert port.upsampling_mode == "mw"

    assert port.to_dict(include_defaults=False) == {
        "__class__": "quam.components.ports.analog_outputs.BBFEMAnalogOutputPort",
        "controller_id": "con1",
        "fem_id": 1,
        "port_id": 2,
    }

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
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
                        "type": "BB",
                        "analog_outputs": {
                            2: {
                                "delay": 0,
                                "shareable": False,
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
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "offset": 0.1,
    }

    port.sampling_rate = 2e9

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "sampling_rate": 2e9,
        "offset": 0.1,
    }


def test_bb_fem_analog_output_port_filter():
    port = BBFEMAnalogOutputPort("con1", 1, 2)
    port.feedforward_filter = [0.7, 0.2, 0.1]

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"feedforward": [0.7, 0.2, 0.1]},
    }


def test_bb_fem_analog_output_port_exponential_filter():
    port = BBFEMAnalogOutputPort("con1", 1, 2)
    port.exponential_filter = [(10, 0.1), (20, 0.2)]
    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"exponential": [(10, 0.1), (20, 0.2)]},
    }

    # Adding feedback filter should raise ValueError due to mutual exclusivity
    port.feedback_filter = [0.3, 0.4, 0.5]
    with pytest.raises(
        ValueError,
        match="'exponential_filter' / 'high_pass_filter' / 'exponential_dc_gain'",
    ):
        port.get_port_properties()


def test_bb_fem_analog_output_port_exponential_dc_gain():
    port = BBFEMAnalogOutputPort("con1", 1, 2)
    port.exponential_dc_gain = 0.5

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"exponential_dc_gain": 0.5},
    }


def test_bb_fem_analog_output_port_high_pass_filter():
    port = BBFEMAnalogOutputPort("con1", 1, 2)
    port.high_pass_filter = 1e-3

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"high_pass": 1e-3},
    }


def test_bb_fem_analog_output_port_exponential_dc_gain_with_high_pass():
    port = BBFEMAnalogOutputPort("con1", 1, 2)
    port.exponential_dc_gain = 0.5
    port.high_pass_filter = 1e-3

    assert port.get_port_properties() == {
        "delay": 0,
        "shareable": False,
        "sampling_rate": 1e9,
        "upsampling_mode": "mw",
        "filter": {"exponential_dc_gain": 0.5, "high_pass": 1e-3},
    }


def test_bb_fem_analog_output_port_exponential_dc_gain_and_feedback_mutually_exclusive():
    port = BBFEMAnalogOutputPort("con1", 1, 2)
    port.exponential_dc_gain = 0.5
    port.feedback_filter = [0.3, 0.4]

    with pytest.raises(
        ValueError,
        match="'exponential_filter' / 'high_pass_filter' / 'exponential_dc_gain'",
    ):
        port.get_port_properties()


def test_bb_fem_analog_output_port_high_pass_and_feedback_mutually_exclusive():
    port = BBFEMAnalogOutputPort("con1", 1, 2)
    port.high_pass_filter = 1e-3
    port.feedback_filter = [0.3, 0.4]

    with pytest.raises(
        ValueError,
        match="'exponential_filter' / 'high_pass_filter' / 'exponential_dc_gain'",
    ):
        port.get_port_properties()


def test_bb_fem_analog_output_port_no_output_mode():
    port = BBFEMAnalogOutputPort("con1", 1, 2)
    assert not hasattr(port, "output_mode")
    assert "output_mode" not in port.get_port_properties()


def test_bb_fem_analog_input_port():
    with pytest.raises(TypeError):
        BBFEMAnalogInputPort()

    port = BBFEMAnalogInputPort("con1", 1, 2)
    assert port.controller_id == "con1"
    assert port.fem_id == 1
    assert port.port_id == 2
    assert port.port_tuple == ("con1", 1, 2)

    assert port.port_type == "analog_input"
    assert port.offset is None
    assert port.gain_db == 0
    assert port.shareable == False
    assert port.sampling_rate == 1e9

    assert port.to_dict(include_defaults=False) == {
        "__class__": "quam.components.ports.analog_inputs.BBFEMAnalogInputPort",
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
                        "type": "BB",
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
