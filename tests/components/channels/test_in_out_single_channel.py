import pytest
from quam.components import *
from quam.components.ports.analog_inputs import OPXPlusAnalogInputPort
from quam.components.ports.analog_outputs import OPXPlusAnalogOutputPort


def test_in_out_single_channel_empty_error():
    with pytest.raises(TypeError):
        InOutSingleChannel()


def test_in_out_single_channel_no_id_error():
    channel = InOutSingleChannel(
        opx_output=("con1", 1),
        opx_input=("con1", 2),
    )
    with pytest.raises(AttributeError):
        channel.name


def test_in_out_single_channel():
    channel = InOutSingleChannel(
        id=1,
        opx_output=("con1", 1),
        opx_input=("con1", 2),
    )

    cfg = {"controllers": {}, "elements": {}}

    channel.apply_to_config(cfg)

    expected_cfg = {
        "controllers": {
            "con1": {
                "analog_inputs": {2: {"gain_db": 0, "shareable": False}},
                "analog_outputs": {1: {"delay": 0, "shareable": False}},
            }
        },
        "elements": {
            "ch1": {
                "operations": {},
                "outputs": {"out1": ("con1", 2)},
                "singleInput": {"port": ("con1", 1)},
                "smearing": 0,
                "time_of_flight": 24,
            }
        },
    }

    assert cfg == expected_cfg


def test_in_out_single_channel_ports():
    channel = InOutSingleChannel(
        id=1,
        opx_output=OPXPlusAnalogOutputPort("con1", 1),
        opx_input=OPXPlusAnalogInputPort("con1", 2),
    )

    cfg = {"controllers": {}, "elements": {}}

    channel.apply_to_config(cfg)
    channel.opx_output.apply_to_config(cfg)
    channel.opx_input.apply_to_config(cfg)

    expected_cfg = {
        "controllers": {
            "con1": {
                "analog_inputs": {2: {"gain_db": 0, "shareable": False}},
                "analog_outputs": {1: {"delay": 0, "shareable": False}},
            }
        },
        "elements": {
            "ch1": {
                "operations": {},
                "outputs": {"out1": ("con1", 2)},
                "singleInput": {"port": ("con1", 1)},
                "smearing": 0,
                "time_of_flight": 24,
            }
        },
    }

    assert cfg == expected_cfg
