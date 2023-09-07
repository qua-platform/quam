import numpy as np

from quam_components.components.pulses import *


def test_drag_pulse():
    drag_pulse = DragPulse(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20
    )

    assert drag_pulse.operation == "control"
    assert drag_pulse.length == 20
    assert drag_pulse.get_attrs() == {
        "length": 20,
        "digital_marker": None,
        "amplitude": 1,
        "sigma": 4,
        "alpha": 2,
        "anharmonicity": 200000000.0,
        "detuning": 0.0,
        "subtracted": True,
    }

    from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

    assert DragPulse.waveform_function is drag_gaussian_pulse_waveforms

    assert drag_pulse._get_waveform_kwargs() == {
        "amplitude": 1,
        "sigma": 4,
        "alpha": 2,
        "anharmonicity": 200e6,
        "detuning": 0.0,
        "subtracted": True,
        "length": 20,
    }

    waveform = drag_pulse.calculate_waveform()
    assert len(waveform) == 20
    assert isinstance(waveform, np.ndarray)
    assert np.iscomplexobj(waveform)
