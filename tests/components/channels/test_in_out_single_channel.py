import pytest
from quam.components import *


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

    assert cfg == {
        "controllers": {
            "con1": {
                "analog_inputs": {2: {}},
                "analog_outputs": {1: {}},
                "digital_outputs": {},
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
