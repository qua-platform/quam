import pytest
from quam.components import IQChannel


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

    assert channel.intermediate_frequency == 0.0
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
