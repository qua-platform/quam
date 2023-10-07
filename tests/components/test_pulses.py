import numpy as np

from quam.components import *


def test_drag_pulse():
    drag_pulse = pulses.DragPulse(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20, rotation_angle=0
    )

    assert drag_pulse.operation == "control"
    assert drag_pulse.length == 20
    assert drag_pulse.get_attrs() == {
        "length": 20,
        "rotation_angle": 0.0,
        "digital_marker": None,
        "amplitude": 1,
        "sigma": 4,
        "alpha": 2,
        "anharmonicity": 200000000.0,
        "detuning": 0.0,
        "subtracted": True,
    }

    from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms

    waveform = drag_pulse.calculate_waveform()
    assert len(waveform) == 20
    assert isinstance(waveform, np.ndarray)
    assert np.iscomplexobj(waveform)


def test_pulse_emitter():
    pulse_emitter = PulseEmitter()
    d = pulse_emitter.to_dict()

    assert d == {}


def test_IQ_channel():
    IQ_channel = IQChannel(
        mixer=Mixer(),
        local_oscillator=None,
        output_port_I=0,
        output_port_Q=1,
        intermediate_frequency=100e6,
    )
    d = IQ_channel.to_dict()
    assert d == {
        "mixer": {},
        "output_port_I": 0,
        "output_port_Q": 1,
        "intermediate_frequency": 100e6,
        "local_oscillator": None,
    }
