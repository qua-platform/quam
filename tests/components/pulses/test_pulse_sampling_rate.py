import pytest
from quam.components import pulses, ports, channels


@pytest.fixture
def pulse():
    return pulses.GaussianPulse(length=60, amplitude=0, sigma=20)


def test_pulse_default_sampling_rate(pulse):
    assert len(pulse.waveform_function()) == 60


def test_pulse_sampling_rate_opx_plus_port(pulse):
    port = ports.OPXPlusAnalogOutputPort(controller_id="con1", port_id=1)
    channel = channels.SingleChannel(opx_output=port, operations={"pulse": pulse})

    assert len(pulse.waveform_function()) == 60


def test_pulse_sampling_rate_lf_fem_port(pulse):
    port = ports.LFFEMAnalogOutputPort(controller_id="con1", fem_id=1, port_id=1)
    channel = channels.SingleChannel(opx_output=port, operations={"pulse": pulse})

    assert len(pulse.waveform_function()) == 60

    port.sampling_rate = 2e9
    assert len(pulse.waveform_function()) == 120


def test_pulse_sampling_rate_mw_fem_port(pulse):
    port = ports.MWFEMAnalogOutputPort(
        controller_id="con1", fem_id=1, port_id=1, band=1
    )
    channel = channels.SingleChannel(opx_output=port, operations={"pulse": pulse})

    assert len(pulse.waveform_function()) == 60

    port.sampling_rate = 2e9
    assert len(pulse.waveform_function()) == 120
