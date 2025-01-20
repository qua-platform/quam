import pytest
from quam.core import *
from quam.components import *
from quam.components.channels import Channel, IQChannel, SingleChannel


def test_channel():
    channel = Channel()
    d = channel.to_dict()

    assert d == {}


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
        "opx_output_I": 0,
        "opx_output_Q": 1,
        "intermediate_frequency": 100e6,
        "frequency_converter_up": {
            "__class__": "quam.components.hardware.FrequencyConverter",
            "mixer": {},
            "local_oscillator": {},
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

    with pytest.raises(IndexError):
        single_channel.play("X180", validate=False)

    single_channel.operations["X180"] = pulses.DragPulse(
        length=16,
        axis_angle=0,
        amplitude=1,
        sigma=12,
        alpha=0.1,
        anharmonicity=200e6,
    )

    with pytest.raises(IndexError):
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

    gaussian_pulse = pulses.GaussianPulse(
        length=16, amplitude=1.0, sigma=4.0, axis_angle=None
    )
    IQ_channel.operations["gaussian"] = gaussian_pulse

    cfg = {"pulses": {}, "waveforms": {}}
    gaussian_pulse.apply_to_config(cfg)

    pulse_config = cfg["pulses"][gaussian_pulse.pulse_name]
    i_waveform_name = pulse_config["waveforms"]["I"]
    q_waveform_name = pulse_config["waveforms"]["Q"]

    i_waveform = cfg["waveforms"][i_waveform_name]["samples"]
    q_waveform = cfg["waveforms"][q_waveform_name]["samples"]

    assert isinstance(i_waveform, list), "I waveform should be a list"
    assert isinstance(q_waveform, list), "Q waveform should be a list"


def test_complex_arbitrary_waveform_iq_channel_list_conversion():
    """Test that complex arbitrary waveforms on IQ channels convert both I and Q to lists"""
    import numpy as np

    IQ_channel = IQChannel(
        id="IQ",
        opx_output_I=("con1", 1),
        opx_output_Q=("con1", 2),
        intermediate_frequency=100e6,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(), local_oscillator=LocalOscillator()
        ),
    )

    @quam_dataclass
    class CustomComplexPulse(pulses.Pulse):
        amplitude: float = 1.0

        def waveform_function(self):
            return np.array([1 + 1j, 2 + 2j, 3 + 3j, 4 + 4j])

    complex_pulse = CustomComplexPulse(length=4)
    IQ_channel.operations["complex"] = complex_pulse

    cfg = {"pulses": {}, "waveforms": {}}
    complex_pulse.apply_to_config(cfg)

    pulse_config = cfg["pulses"][complex_pulse.pulse_name]
    i_waveform_name = pulse_config["waveforms"]["I"]
    q_waveform_name = pulse_config["waveforms"]["Q"]

    i_waveform = cfg["waveforms"][i_waveform_name]["samples"]
    q_waveform = cfg["waveforms"][q_waveform_name]["samples"]

    assert isinstance(i_waveform, list), "I waveform should be a list"
    assert isinstance(q_waveform, list), "Q waveform should be a list"
