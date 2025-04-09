from collections.abc import Iterable
import numpy as np
import pytest
from quam.components.pulses import WaveformPulse


def test_waveform_pulse_length():
    pulse = WaveformPulse(waveform_I=[1, 2, 3])
    assert pulse.length == 3

    pulse.waveform_I = [1, 2, 3, 4]

    with pytest.raises(AttributeError):
        pulse.length = 5

    assert pulse.length == 4


def test_waveform_pulse_IQ():
    pulse = WaveformPulse(waveform_I=[1, 2, 3], waveform_Q=[4, 5, 6])
    assert np.all(
        pulse.waveform_function() == np.array([1, 2, 3]) + 1.0j * np.array([4, 5, 6])
    )
    assert pulse.length


def test_waveform_pulse_IQ_mismatch():
    pulse = WaveformPulse(waveform_I=[1, 2, 3], waveform_Q=[4, 5])
    with pytest.raises(ValueError):
        pulse.waveform_function()


def test_waveform_pulse_to_dict():
    pulse = WaveformPulse(waveform_I=[1, 2, 3], waveform_Q=[4, 5, 6])
    assert pulse.to_dict() == {
        "__class__": "quam.components.pulses.WaveformPulse",
        "waveform_I": [1, 2, 3],
        "waveform_Q": [4, 5, 6],
    }


def test_waveform_pulse_length_error():
    with pytest.raises(AttributeError):
        pulse = WaveformPulse(waveform_I=[1, 2, 3], length=11)

    pulse = WaveformPulse(waveform_I=[1, 2, 3])
    with pytest.raises(AttributeError):
        pulse.length = 11
