"""
Waveform and integration-weight helper functions, originally from qualang-tools.
Vendored here to remove the qualang-tools runtime dependency.
"""

import numpy as np
from scipy.signal.windows import gaussian, blackman


def drag_gaussian_pulse_waveforms(
    amplitude, length, sigma, alpha, anharmonicity, detuning=0.0, subtracted=True, **kwargs
):
    if alpha != 0 and anharmonicity == 0:
        raise ValueError("Cannot create a DRAG pulse with `anharmonicity=0`")
    t = np.arange(length, dtype=int)
    center = (length - 1) / 2
    gauss_wave = amplitude * np.exp(-((t - center) ** 2) / (2 * sigma**2))
    gauss_der_wave = (
        amplitude * (-2 * 1e9 * (t - center) / (2 * sigma**2)) * np.exp(-((t - center) ** 2) / (2 * sigma**2))
    )
    if subtracted:
        gauss_wave = gauss_wave - gauss_wave[-1]
    z = gauss_wave + 1j * 0
    if alpha != 0:
        z += 1j * gauss_der_wave * (alpha / (2 * np.pi * anharmonicity - 2 * np.pi * detuning))
        z *= np.exp(1j * 2 * np.pi * detuning * t * 1e-9)
    return z.real.tolist(), z.imag.tolist()


def drag_cosine_pulse_waveforms(amplitude, length, alpha, anharmonicity, detuning=0.0, **kwargs):
    if alpha != 0 and anharmonicity == 0:
        raise ValueError("Cannot create a DRAG pulse with `anharmonicity=0`")
    t = np.arange(length, dtype=int)
    end_point = length - 1
    cos_wave = 0.5 * amplitude * (1 - np.cos(t * 2 * np.pi / end_point))
    sin_wave = 0.5 * amplitude * (2 * np.pi / end_point * 1e9) * np.sin(t * 2 * np.pi / end_point)
    z = cos_wave + 1j * 0
    if alpha != 0:
        z += 1j * sin_wave * (alpha / (2 * np.pi * anharmonicity - 2 * np.pi * detuning))
        z *= np.exp(1j * 2 * np.pi * detuning * t * 1e-9)
    return z.real.tolist(), z.imag.tolist()


def flattop_gaussian_waveform(amplitude, flat_length, rise_fall_length, return_part="all", **kwargs):
    gauss_wave = amplitude * gaussian(2 * rise_fall_length, rise_fall_length / 5)
    rise_part = gauss_wave[:rise_fall_length].tolist()
    if return_part == "all":
        return rise_part + [amplitude] * flat_length + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    raise ValueError("'return_part' must be 'all', 'rise', or 'fall'")


def flattop_cosine_waveform(amplitude, flat_length, rise_fall_length, return_part="all", **kwargs):
    rise_part = (amplitude * 0.5 * (1 - np.cos(np.linspace(0, np.pi, rise_fall_length)))).tolist()
    if return_part == "all":
        return rise_part + [amplitude] * flat_length + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    raise ValueError("'return_part' must be 'all', 'rise', or 'fall'")


def flattop_tanh_waveform(amplitude, flat_length, rise_fall_length, return_part="all", **kwargs):
    rise_part = (amplitude * 0.5 * (1 + np.tanh(np.linspace(-4, 4, rise_fall_length)))).tolist()
    if return_part == "all":
        return rise_part + [amplitude] * flat_length + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    raise ValueError("'return_part' must be 'all', 'rise', or 'fall'")


def flattop_blackman_waveform(amplitude, flat_length, rise_fall_length, return_part="all", **kwargs):
    blackman_wave = amplitude * blackman(2 * rise_fall_length)
    rise_part = blackman_wave[:rise_fall_length].tolist()
    if return_part == "all":
        return rise_part + [amplitude] * flat_length + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    raise ValueError("'return_part' must be 'all', 'rise', or 'fall'")


def blackman_integral_waveform(pulse_length, v_start, v_end, **kwargs):
    time = np.arange(int(pulse_length), dtype=float)
    waveform = v_start + (
        time / (pulse_length - 1)
        - (25 / (42 * np.pi)) * np.sin(2 * np.pi * time / (pulse_length - 1))
        + (1 / (21 * np.pi)) * np.sin(4 * np.pi * time / (pulse_length - 1))
    ) * (v_end - v_start)
    return waveform.tolist()


def _round_to_fixed_point_accuracy(x, accuracy=2**-15):
    return np.round(x / accuracy) * accuracy


def compress_integration_weights(integration_weights, N=100):
    integration_weights = np.array(integration_weights)
    while len(integration_weights) > N:
        diffs = np.abs(np.diff(integration_weights, axis=0)[:, 0])
        idx = np.argmin(diffs)
        t1, t2 = integration_weights[idx, 1], integration_weights[idx + 1, 1]
        w1, w2 = integration_weights[idx, 0], integration_weights[idx + 1, 0]
        integration_weights[idx, 0] = (w1 * t1 + w2 * t2) / (t1 + t2)
        integration_weights[idx, 1] = t1 + t2
        integration_weights = np.delete(integration_weights, idx + 1, 0)
    return list(zip(integration_weights.T[0].tolist(), integration_weights.T[1].astype(int).tolist()))


def convert_integration_weights(integration_weights, N=100, accuracy=2**-15):
    integration_weights = _round_to_fixed_point_accuracy(np.array(integration_weights), accuracy)
    changes_indices = np.where(np.abs(np.diff(integration_weights)) > 0)[0].tolist()
    prev_index = -1
    new_weights = []
    for curr_index in changes_indices + [len(integration_weights) - 1]:
        new_weights.append((integration_weights[curr_index].tolist(), round(4 * (curr_index - prev_index))))
        prev_index = curr_index
    return compress_integration_weights(new_weights, N=N)
