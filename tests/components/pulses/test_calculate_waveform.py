import numpy as np

from quam.components.pulses import Pulse
from quam.core import quam_dataclass


@quam_dataclass
class FloatTuplePulse(Pulse):
    i: float
    q: float

    def waveform_function(self):
        return (self.i, self.q)


@quam_dataclass
class NdarrayTuplePulse(Pulse):
    def waveform_function(self):
        return (np.array([0.1, 0.2, 0.3, 0.4]), np.array([0.5, 0.6, 0.7, 0.8]))


def test_calculate_waveform_float_tuple_returns_complex():
    pulse = FloatTuplePulse(length=16, i=0.1, q=0.2)
    result = pulse.calculate_waveform()
    assert result == complex(0.1, 0.2)


def test_calculate_waveform_float_tuple_type():
    pulse = FloatTuplePulse(length=16, i=0.1, q=0.2)
    result = pulse.calculate_waveform()
    assert isinstance(result, complex)


def test_calculate_waveform_ndarray_tuple_returns_complex_ndarray():
    pulse = NdarrayTuplePulse(length=4)
    result = pulse.calculate_waveform()
    expected = np.array([0.1, 0.2, 0.3, 0.4]) + 1.0j * np.array([0.5, 0.6, 0.7, 0.8])
    assert np.all(result == expected)
