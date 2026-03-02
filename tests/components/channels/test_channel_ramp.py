import pytest

from qm import qua
from qm.qua import ramp
from quam.components.channels import Channel, SingleChannel


# ---------------------------------------------------------------------------
# Channel.ramp()
# ---------------------------------------------------------------------------


def test_channel_ramp_calls_play(mocker):
    mock_play = mocker.patch("quam.components.channels.play")
    mock_qua_ramp = mocker.patch("quam.components.channels.qua_ramp")
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
    mock_ramp_to_zero = mocker.patch("quam.components.channels.qua_ramp_to_zero")

    channel = Channel(id="test_channel")
    channel.ramp_to_zero()

    mock_ramp_to_zero.assert_called_once_with("test_channel", duration=None)


def test_channel_ramp_to_zero_with_duration(mocker):
    mock_ramp_to_zero = mocker.patch("quam.components.channels.qua_ramp_to_zero")

    channel = Channel(id="test_channel")
    channel.ramp_to_zero(duration=500)

    mock_ramp_to_zero.assert_called_once_with("test_channel", duration=500)


def test_channel_ramp_to_zero_inside_program():
    channel = Channel(id="test_channel")

    with qua.program() as prog:
        channel.ramp_to_zero()


# ---------------------------------------------------------------------------
# Channel.play() accepts ramp() object without validate=False
# ---------------------------------------------------------------------------


def test_play_with_ramp_object_skips_validation(mocker):
    mock_play = mocker.patch("quam.components.channels.play")
    ramp_obj = ramp(0.0001)

    channel = Channel(id="test_channel")
    # Should not raise KeyError even though "ramp_obj" is not in operations
    channel.play(ramp_obj, duration=1000)

    mock_play.assert_called_once_with(
        pulse=ramp_obj,
        element="test_channel",
        duration=1000,
        condition=None,
        chirp=None,
        truncate=None,
        timestamp_stream=None,
        continue_chirp=False,
        target="",
    )


def test_play_with_ramp_object_inside_program():
    channel = Channel(id="test_channel")

    with qua.program() as prog:
        channel.play(ramp(0.0001), duration=1000)


def test_play_with_string_still_validates():
    channel = Channel(id="test_channel")

    with pytest.raises(KeyError, match="not found in channel"):
        channel.play("nonexistent_pulse")


def test_play_with_ramp_object_no_validate_false_needed(mocker):
    """Previously required validate=False — now works without it."""
    mock_play = mocker.patch("quam.components.channels.play")
    ramp_obj = ramp(0.0005)

    channel = Channel(id="test_channel")
    # validate=True is the default — must not raise
    channel.play(ramp_obj, duration=500)

    assert mock_play.called
