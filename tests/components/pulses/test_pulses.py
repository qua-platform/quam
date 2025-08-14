import numpy as np
import pytest

from quam.core import *
from quam.components import *
from quam.components.channels import Channel, IQChannel, SingleChannel
from quam.utils.dataclass import get_dataclass_attr_annotations

try:
    from qm.exceptions import NoScopeFoundException
except ImportError:
    NoScopeFoundException = IndexError

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


def test_channel():
    channel = Channel()
    d = channel.to_dict()

    assert d == {
        "__class__": "quam.components.channels.Channel",
    }


def test_IQ_channel():
    IQ_channel = IQChannel(
        opx_output_I=0,
        opx_output_Q=1,
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )
    d = IQ_channel.to_dict()
    assert d == {
        "__class__": "quam.components.channels.IQChannel",
        "opx_output_I": 0,
        "opx_output_Q": 1,
        "intermediate_frequency": 100e6,
        "frequency_converter_up": {
            "__class__": "quam.components.hardware.FrequencyConverter",
            "mixer": {"__class__": "quam.components.hardware.Mixer"},
            "local_oscillator": {
                "__class__": "quam.components.hardware.LocalOscillator",
            },
        },
    }


def test_single_pulse_IQ_channel():
    IQ_channel = IQChannel(
        id="IQ",
        opx_output_I=0,
        opx_output_Q=1,
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )
    IQ_channel.operations["X180"] = pulses.GaussianPulse(
        length=16, amplitude=1, sigma=12
    )

    cfg = {"pulses": {}, "waveforms": {}}
    pulse = IQ_channel.operations["X180"]

    # axis_angle = None translates to all signal on I
    pulse.apply_to_config(cfg)

    pulse.axis_angle = 90
    pulse.apply_to_config(cfg)


def test_IQ_pulse_single_channel():
    single_channel = SingleChannel(
        id="single",
        opx_output=0,
    )
    single_channel.operations["X180"] = pulses.DragPulse(
        length=16,
        axis_angle=0,
        amplitude=1,
        sigma=12,
        alpha=0.1,
        anharmonicity=200e6,
    )

    cfg = {"pulses": {}, "waveforms": {}}
    pulse = single_channel.operations["X180"]

    with pytest.raises(ValueError) as exc_info:
        pulse.apply_to_config(cfg)
    error_message = "Waveform type 'IQ' not allowed for SingleChannel 'single'"
    assert str(exc_info.value) == error_message


def test_IQ_pulse_play_validate():
    single_channel = SingleChannel(
        id="single",
        opx_output=0,
    )

    with pytest.raises(KeyError):
        single_channel.play("X180")

    with pytest.raises(NoScopeFoundException):
        single_channel.play("X180", validate=False)

    single_channel.operations["X180"] = pulses.DragPulse(
        length=16,
        axis_angle=0,
        amplitude=1,
        sigma=12,
        alpha=0.1,
        anharmonicity=200e6,
    )

    with pytest.raises(NoScopeFoundException):
        single_channel.play("X180")


def test_pulse_parent_channel():
    pulse = pulses.SquarePulse(length=60, amplitude=0)
    assert pulse.parent is None
    assert pulse.channel is None

    channel = SingleChannel(id="single", opx_output=0)
    pulse.parent = channel
    assert pulse.parent is channel
    assert pulse.channel is channel


def test_pulse_parent_parent_channel():
    pulse = pulses.SquarePulse(length=60, amplitude=0)
    channel = SingleChannel(id="single", opx_output=0)
    channel.operations["pulse"] = pulse
    assert pulse.parent is channel.operations
    assert pulse.channel is channel


@quam_dataclass
class QuamTestPulseReferenced(QuamRoot):
    channel: SingleChannel


def test_pulses_referenced():
    channel = SingleChannel(id="single", opx_output=("con1", 1))
    machine = QuamTestPulseReferenced(channel=channel)

    pulse = pulses.SquarePulse(length=60, amplitude=0)
    channel.operations["pulse"] = pulse
    channel.operations["pulse_referenced"] = "#./pulse"

    assert (
        channel.operations["pulse_referenced"] == channel.operations["pulse"] == pulse
    )

    state = machine.to_dict()

    machine_loaded = QuamTestPulseReferenced.load(state)

    pulse_loaded = machine_loaded.channel.operations["pulse"]
    assert isinstance(pulse_loaded, pulses.SquarePulse)
    assert pulse_loaded.to_dict() == pulse.to_dict()

    assert machine_loaded.channel.operations["pulse_referenced"] == pulse_loaded
    assert (
        machine_loaded.channel.operations.get_raw_value("pulse_referenced")
        == "#./pulse"
    )


def test_pulse_attr_annotations():
    from quam.components import pulses

    attr_annotations = get_dataclass_attr_annotations(pulses.SquareReadoutPulse)

    assert list(attr_annotations["required"]) == ["length", "amplitude"]


def test_deprecated_drag_pulse():
    with pytest.warns(
        DeprecationWarning,
        match="DragPulse is deprecated. Use DragGaussianPulse instead.",
    ):
        pulses.DragPulse(
            axis_angle=0, amplitude=1, sigma=4, alpha=2, anharmonicity=200e6, length=20
        )


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


def test_arbitrary_waveform_iq_channel_list_conversion():
    """Test that arbitrary waveforms on IQ channels convert both I and Q to lists"""
    IQ_channel = IQChannel(
        id="IQ",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )

    # Create a Gaussian pulse that returns an arbitrary waveform (numpy array)
    gaussian_pulse = pulses.GaussianPulse(
        length=16, amplitude=1.0, sigma=4.0, axis_angle=None
    )
    IQ_channel.operations["gaussian"] = gaussian_pulse

    cfg = {"pulses": {}, "waveforms": {}}
    gaussian_pulse.apply_to_config(cfg)

    # Check that both I and Q waveforms are lists
    pulse_config = cfg["pulses"][gaussian_pulse.pulse_name]
    i_waveform_name = pulse_config["waveforms"]["I"]
    q_waveform_name = pulse_config["waveforms"]["Q"]

    i_waveform = cfg["waveforms"][i_waveform_name]["samples"]
    q_waveform = cfg["waveforms"][q_waveform_name]["samples"]

    assert isinstance(i_waveform, list), "I waveform should be a list"
    assert isinstance(q_waveform, list), "Q waveform should be a list"
    assert len(i_waveform) == 16, "I waveform should have correct length"
    assert len(q_waveform) == 16, "Q waveform should have correct length"
    # Q waveform should be all zeros since axis_angle=None
    assert all(q == 0.0 for q in q_waveform), "Q waveform should be all zeros"


def test_complex_arbitrary_waveform_iq_channel_list_conversion():
    """Test that complex arbitrary waveforms on IQ channels convert both I and Q to lists"""
    from quam.components.channels import IQChannel, MWChannel

    IQ_channel = IQChannel(
        id="IQ",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )

    # Create a custom pulse that returns a complex waveform
    @quam_dataclass
    class CustomComplexPulse(pulses.Pulse):
        amplitude: float = 1.0

        def waveform_function(self):
            # Return a complex numpy array
            return np.array([1 + 1j, 2 + 2j, 3 + 3j, 4 + 4j])

    complex_pulse = CustomComplexPulse(length=4)
    IQ_channel.operations["complex"] = complex_pulse

    cfg = {"pulses": {}, "waveforms": {}}
    complex_pulse.apply_to_config(cfg)

    # Check that both I and Q waveforms are lists
    pulse_config = cfg["pulses"][complex_pulse.pulse_name]
    i_waveform_name = pulse_config["waveforms"]["I"]
    q_waveform_name = pulse_config["waveforms"]["Q"]

    i_waveform = cfg["waveforms"][i_waveform_name]["samples"]
    q_waveform = cfg["waveforms"][q_waveform_name]["samples"]

    assert isinstance(i_waveform, list), "I waveform should be a list"
    assert isinstance(q_waveform, list), "Q waveform should be a list"
    assert len(i_waveform) == 4, "I waveform should have correct length"
    assert len(q_waveform) == 4, "Q waveform should have correct length"
    assert i_waveform == [1.0, 2.0, 3.0, 4.0], "I waveform should match real part"
    assert q_waveform == [1.0, 2.0, 3.0, 4.0], "Q waveform should match imaginary part"
