import pytest

from qm import qua
from quam.components import pulses, SingleChannel


@pytest.fixture
def ch():
    pulse = pulses.GaussianPulse(
        amplitude=1,
        length=10,
        sigma=1,
    )
    channel = SingleChannel(
        id="test_channel",
        operations={"pulse": pulse},
        opx_output=("con1", 1),
    )
    return channel


def test_pulse_no_amplitude_scale(ch):
    with qua.program():
        ch.play("pulse")


def test_pulse_float_amplitude_scale(ch):
    with qua.program():
        ch.play("pulse", amplitude_scale=0.5)


def test_pulse_amplitude_scale_qua_var(ch):
    with qua.program():
        a = qua.declare(qua.fixed)
        ch.play("pulse", amplitude_scale=a)


def test_pulse_amplitude_scale_qua_var_binary_op(ch):
    with qua.program():
        a = qua.declare(qua.fixed)
        ch.play("pulse", amplitude_scale=a * 0.1)


def test_pulse_amplitude_scale_float_list(ch):
    with qua.program():
        ch.play("pulse", amplitude_scale=[0, 0, 0, 1])


def test_pulse_amplitude_scale_float_list_qua_var(ch):
    with qua.program():
        a = qua.declare(qua.fixed)
        ch.play("pulse", amplitude_scale=[0, 0, 0, a])
