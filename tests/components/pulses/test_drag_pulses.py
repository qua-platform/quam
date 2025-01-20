import numpy as np
import pytest
from quam.core import *
from quam.components import *


def test_drag_gaussian_pulse():
    drag_pulse = pulses.DragGaussianPulse(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20, axis_angle=0
    )

    assert drag_pulse.operation == "control"
    assert drag_pulse.length == 20
    assert drag_pulse.get_attrs() == {
        "id": None,
        "length": 20,
        "axis_angle": 0.0,
        "digital_marker": None,
        "amplitude": 1,
        "sigma": 4,
        "alpha": 2,
        "anharmonicity": 200000000.0,
        "detuning": 0.0,
        "subtracted": True,
    }

    waveform = drag_pulse.calculate_waveform()
    assert len(waveform) == 20
    assert isinstance(waveform, np.ndarray)
    assert np.iscomplexobj(waveform)


def test_drag_cosine_pulse():
    drag_pulse = pulses.DragCosinePulse(
        amplitude=1, alpha=2, anharmonicity=200e6, length=20, axis_angle=0
    )

    assert drag_pulse.operation == "control"
    assert drag_pulse.length == 20
    assert drag_pulse.get_attrs() == {
        "id": None,
        "length": 20,
        "axis_angle": 0.0,
        "digital_marker": None,
        "amplitude": 1,
        "alpha": 2,
        "anharmonicity": 200000000.0,
        "detuning": 0.0,
    }

    waveform = drag_pulse.calculate_waveform()
    assert len(waveform) == 20
    assert isinstance(waveform, np.ndarray)
    assert np.iscomplexobj(waveform)


def test_deprecated_drag_pulse():
    with pytest.warns(
        DeprecationWarning,
        match="DragPulse is deprecated. Use DragGaussianPulse instead.",
    ):
        pulses.DragPulse(
            axis_angle=0, amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20
        )
