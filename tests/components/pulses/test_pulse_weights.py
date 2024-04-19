import numpy as np
from quam.components import pulses


def compare_integration_weights(expected_weights, weights):
    for key, val in expected_weights.items():
        assert key in weights
        assert len(val) == len(weights[key])
        for weight_expected, weight in zip(val, weights[key]):
            assert np.isclose(weight_expected[0], weight[0], atol=1e-5)
            assert weight_expected[1] == weight[1]


def test_constant_readout_pulse_integration_weights_default():
    pulse = pulses.SquareReadoutPulse(length=100, amplitude=1)

    weights = pulse.integration_weights_function()
    expected_weights = {
        "real": [(1, 100)],
        "imag": [(0, 100)],
        "minus_real": [(-1, 100)],
        "minus_imag": [(0, 100)],
    }
    compare_integration_weights(expected_weights, weights)


def test_empty_integration_weights():
    for weights in ([], np.array([]), None):
        pulse = pulses.SquareReadoutPulse(
            length=100, amplitude=1, integration_weights=weights
        )

        weights = pulse.integration_weights_function()
        expected_weights = {
            "real": [(1, 100)],
            "imag": [(0, 100)],
            "minus_real": [(-1, 100)],
            "minus_imag": [(0, 100)],
        }
        compare_integration_weights(expected_weights, weights)


def test_constant_readout_pulse_integration_weights_phase_shift():
    pulse = pulses.SquareReadoutPulse(
        length=100, amplitude=1, integration_weights_angle=np.pi / 2
    )

    weights = pulse.integration_weights_function()
    expected_weights = {
        "real": [(np.cos(np.pi / 2), 100)],
        "imag": [(np.sin(np.pi / 2), 100)],
        "minus_real": [(-np.cos(np.pi / 2), 100)],
        "minus_imag": [(-np.sin(np.pi / 2), 100)],
    }
    compare_integration_weights(expected_weights, weights)


def test_constant_readout_pulse_integration_weights_custom_uncompressed():
    pulse = pulses.SquareReadoutPulse(
        length=100,
        amplitude=1,
        integration_weights=[0.4] * 10 + [0.6] * 15,  # units of clock cycle
    )

    weights = pulse.integration_weights_function()
    expected_weights = {
        "real": [(0.4, 40), (0.6, 60)],
        "imag": [(0.0, 40), (0.0, 60)],
        "minus_real": [(-0.4, 40), (-0.6, 60)],
        "minus_imag": [(0.0, 40), (0.0, 60)],
    }
    compare_integration_weights(expected_weights, weights)


def test_constant_readout_pulse_integration_weights_custom_uncompressed_array():
    pulse = pulses.SquareReadoutPulse(
        length=100,
        amplitude=1,
        integration_weights=np.array([0.4] * 10 + [0.6] * 15),  # units of clock cycle
    )

    weights = pulse.integration_weights_function()
    expected_weights = {
        "real": [(0.4, 40), (0.6, 60)],
        "imag": [(0.0, 40), (0.0, 60)],
        "minus_real": [(-0.4, 40), (-0.6, 60)],
        "minus_imag": [(0.0, 40), (0.0, 60)],
    }
    compare_integration_weights(expected_weights, weights)


def test_constant_readout_pulse_integration_weights_custom_compressed():
    pulse = pulses.SquareReadoutPulse(
        length=100, amplitude=1, integration_weights=[(0.4, 40), (0.6, 60)]
    )

    weights = pulse.integration_weights_function()
    expected_weights = {
        "real": [(0.4, 40), (0.6, 60)],
        "imag": [(0, 40), (0, 60)],
        "minus_real": [(-0.4, 40), (-0.6, 60)],
        "minus_imag": [(0, 40), (0, 60)],
    }
    compare_integration_weights(expected_weights, weights)


def test_constant_readout_pulse_integration_weights_custom_compressed_phase():
    pulse = pulses.SquareReadoutPulse(
        length=100,
        amplitude=1,
        integration_weights=[(0.4, 40), (0.6, 60)],
        integration_weights_angle=np.pi / 2,
    )

    weights = pulse.integration_weights_function()
    expected_weights = {
        "real": [(np.cos(np.pi / 2) * 0.4, 40), (np.cos(np.pi / 2) * 0.6, 60)],
        "imag": [(np.sin(np.pi / 2) * 0.4, 40), (np.sin(np.pi / 2) * 0.6, 60)],
        "minus_real": [(np.cos(np.pi / 2) * 0.4, 40), (np.cos(np.pi / 2) * 0.6, 60)],
        "minus_imag": [(np.sin(np.pi / 2) * -0.4, 40), (np.sin(np.pi / 2) * -0.6, 60)],
    }
    compare_integration_weights(expected_weights, weights)
