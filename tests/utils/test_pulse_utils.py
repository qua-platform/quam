from quam.utils.pulse import pulse_str_to_axis_axis_angle


def test_pulse_str_to_axis_angle():
    axis, angle = pulse_str_to_axis_axis_angle("X90")
    assert axis == "X"
    assert angle == 90

    axis, angle = pulse_str_to_axis_axis_angle("Xm90")
    assert axis == "X"
    assert angle == -90

    axis, angle = pulse_str_to_axis_axis_angle("X-90")
    assert axis == "X"
    assert angle == -90
