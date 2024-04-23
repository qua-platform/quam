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
