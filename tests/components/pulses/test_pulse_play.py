import pytest
from quam.components import pulses
from quam.components.channels import SingleChannel


def test_pulse_play(mocker):
    channel = SingleChannel(id="single", opx_output=("con1", 1))
    pulse = pulses.SquarePulse(length=60, amplitude=0)
    channel.operations["pulse"] = pulse

    mock_play = mocker.patch("quam.components.channels.play")
    channel.play("pulse", duration=100)
    mock_play.assert_called_once_with(
        pulse="pulse",
        element="single",
        duration=100,
        condition=None,
        chirp=None,
        truncate=None,
        timestamp_stream=None,
        continue_chirp=False,
        target="",
    )


def test_pulse_play_no_channel(mocker):
    pulse = pulses.SquarePulse(length=60, amplitude=0)
    with pytest.raises(ValueError):
        pulse.play()
