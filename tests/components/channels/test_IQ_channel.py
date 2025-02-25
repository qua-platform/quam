import pytest
from quam.components import IQChannel
from quam.components.ports.analog_outputs import OPXPlusAnalogOutputPort


def test_IQ_channel_set_dc_offset(mocker):
    mocker.patch("quam.components.channels.set_dc_offset")

    channel = IQChannel(
        id="channel",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=None,
    )

    with pytest.raises(TypeError):
        channel.set_dc_offset(0.5)

    with pytest.raises(ValueError):
        channel.set_dc_offset(0.5, "X")

    channel.set_dc_offset(0.5, "I")

    from quam.components.channels import set_dc_offset

    set_dc_offset.assert_called_once_with(
        element="channel", element_input="I", offset=0.5
    )


def test_IQ_channel_inferred_RF_frequency():
    channel = IQChannel(
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=None,
    )

    assert channel.intermediate_frequency is None
    assert channel.LO_frequency == "#./frequency_converter_up/LO_frequency"
    assert channel.RF_frequency == "#./inferred_RF_frequency"
    with pytest.raises(AttributeError):
        channel.inferred_RF_frequency()

    channel.LO_frequency = None
    channel.LO_frequency = 5e9
    channel.intermediate_frequency = 100e6
    assert channel.inferred_RF_frequency == 5.1e9


def test_IQ_channel_inferred_intermediate_frequency():
    channel = IQChannel(
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=None,
        intermediate_frequency="#./inferred_intermediate_frequency",
        LO_frequency=5.1e9,
        RF_frequency=5.2e9,
    )

    assert channel.intermediate_frequency == 100e6

    channel.LO_frequency = None
    with pytest.raises(AttributeError):
        channel.inferred_intermediate_frequency

    channel.LO_frequency = 5.1e9
    channel.RF_frequency = None
    with pytest.raises(AttributeError):
        channel.inferred_intermediate_frequency


def test_IQ_channel_inferred_LO_frequency():
    channel = IQChannel(
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=None,
        intermediate_frequency=100e6,
        LO_frequency="#./inferred_LO_frequency",
        RF_frequency=5.2e9,
    )

    assert channel.LO_frequency == 5.1e9

    channel.RF_frequency = None
    with pytest.raises(AttributeError):
        channel.inferred_LO_frequency

    channel.RF_frequency = 5.2e9
    channel.intermediate_frequency = None
    with pytest.raises(AttributeError):
        channel.inferred_LO_frequency


def test_generate_config(qua_config):
    channel = IQChannel(
        id="out_channel",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        frequency_converter_up=None,
    )

    channel.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_outputs": {
                1: {"delay": 0, "shareable": False},
                2: {"delay": 0, "shareable": False},
            },
        }
    }

    assert qua_config["elements"] == {
        "out_channel": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
            },
            "operations": {},
        }
    }


def test_generate_config_ports(qua_config):
    channel = IQChannel(
        id="out_channel",
        opx_output_I=OPXPlusAnalogOutputPort("con1", 1),
        opx_output_Q=OPXPlusAnalogOutputPort("con1", 2),
        frequency_converter_up=None,
    )

    channel.apply_to_config(qua_config)
    channel.opx_output_I.apply_to_config(qua_config)
    channel.opx_output_Q.apply_to_config(qua_config)

    assert qua_config["controllers"] == {
        "con1": {
            "analog_outputs": {
                1: {"delay": 0, "shareable": False},
                2: {"delay": 0, "shareable": False},
            },
        }
    }

    assert qua_config["elements"] == {
        "out_channel": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
            },
            "operations": {},
        }
    }
