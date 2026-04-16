import pytest

from qm import qua
from quam.components.channels import Channel, SingleChannel

# ---------------------------------------------------------------------------
# Channel.ramp()
# ---------------------------------------------------------------------------


def test_channel_ramp_calls_play(mocker):
    mock_play = mocker.patch("qm.qua.play")
    mock_qua_ramp = mocker.patch("qm.qua.ramp")
    mock_qua_ramp.return_value = "ramp_obj"

    channel = Channel(id="test_channel")
    channel.ramp(slope=0.0001, duration=1000)

    mock_qua_ramp.assert_called_once_with(0.0001)
    mock_play.assert_called_once_with("ramp_obj", "test_channel", duration=1000)


def test_channel_ramp_inside_program():
    channel = Channel(id="test_channel")

    with qua.program() as prog:
        channel.ramp(slope=0.0001, duration=1000)


# ---------------------------------------------------------------------------
# Channel.ramp_to_zero()
# ---------------------------------------------------------------------------


def test_channel_ramp_to_zero_calls_qua(mocker):
    mock_ramp_to_zero = mocker.patch("qm.qua.ramp_to_zero")

    channel = Channel(id="test_channel")
    channel.ramp_to_zero()

    mock_ramp_to_zero.assert_called_once_with("test_channel", duration=None)


def test_channel_ramp_to_zero_with_duration(mocker):
    mock_ramp_to_zero = mocker.patch("qm.qua.ramp_to_zero")

    channel = Channel(id="test_channel")
    channel.ramp_to_zero(duration=500)

    mock_ramp_to_zero.assert_called_once_with("test_channel", duration=500)


def test_channel_ramp_to_zero_inside_program():
    channel = Channel(id="test_channel")

    with qua.program() as prog:
        channel.ramp_to_zero()


def test_play_with_string_still_validates():
    channel = Channel(id="test_channel")

    with pytest.raises(KeyError, match="not found in channel"):
        channel.play("nonexistent_pulse")
