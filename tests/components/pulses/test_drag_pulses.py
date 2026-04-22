import numpy as np
import pytest
from quam.core import *
from quam.components import *
from quam.components import channels, ports


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


def test_drag_gaussian_pulse_sampling_rate():
    drag_pulse = pulses.DragGaussianPulse(
        amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20, axis_angle=0
    )
    port = ports.LFFEMAnalogOutputPort(controller_id="con1", fem_id=1, port_id=1)
    channel = channels.IQChannel(
        id="IQ",
        opx_output_I=port,
        opx_output_Q=ports.LFFEMAnalogOutputPort(
            controller_id="con1", fem_id=1, port_id=2
        ),
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )
    channel.operations["drag"] = drag_pulse

    assert len(drag_pulse.calculate_waveform()) == 20

    port.sampling_rate = 2e9
    assert len(drag_pulse.calculate_waveform()) == 40


def test_drag_cosine_pulse_sampling_rate():
    drag_pulse = pulses.DragCosinePulse(
        amplitude=1, alpha=2, anharmonicity=200e6, length=20, axis_angle=0
    )
    port = ports.LFFEMAnalogOutputPort(controller_id="con1", fem_id=1, port_id=1)
    channel = channels.IQChannel(
        id="IQ",
        opx_output_I=port,
        opx_output_Q=ports.LFFEMAnalogOutputPort(
            controller_id="con1", fem_id=1, port_id=2
        ),
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )
    channel.operations["drag"] = drag_pulse

    assert len(drag_pulse.calculate_waveform()) == 20

    port.sampling_rate = 2e9
    assert len(drag_pulse.calculate_waveform()) == 40
