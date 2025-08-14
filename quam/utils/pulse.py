from typing import Tuple, Optional, Union, Sequence
from typeguard import TypeCheckError, check_type

from qm import qua

from quam.utils.qua_types import ScalarFloat


__all__ = ["pulse_str_to_axis_axis_angle", "add_amplitude_scale_to_pulse_name"]


def pulse_str_to_axis_axis_angle(pulse_str: str) -> Tuple[str, int]:
    """Converts a pulse string to a tuple of axis and angle.

    Args:
        pulse_str: A pulse string, e.g. 'X90'.

    Returns:
        axis (str): The axis, one of "X", "Y" or "Z".
        angle (int): The rotation angle in degrees.

    Raises:
        ValueError: If the pulse string is incorrect
    """
    if pulse_str[0] not in "XYZ":
        raise ValueError(f"Invalid pulse string: {pulse_str}")

    axis = pulse_str[0]
    angle_str = pulse_str[1:]

    if angle_str[0] == "m":
        angle_str = f"-{angle_str[1:]}"

    angle = int(angle_str)

    return axis, angle


def add_amplitude_scale_to_pulse_name(
    pulse_name: str,
    amplitude_scale: Optional[Union[ScalarFloat, Sequence[ScalarFloat]]],
) -> Union[str, tuple]:
    """Adds an amplitude scale to a pulse name.

    Args:
        pulse_name: The name of the pulse.
        amplitude_scale: The amplitude scale to add to the pulse name.
            If None, the pulse name is returned unchanged.

    Returns:
        amplitude_scale == None → pulse_name
        amplitude_scale == float → pulse_name * qua.amp(amplitude_scale)
        amplitude_scale == list[float] → pulse_name * qua.amp(*amplitude_scale)
    """
    if amplitude_scale is None:
        return pulse_name

    try:
        check_type(amplitude_scale, Sequence[ScalarFloat])
        return pulse_name * qua.amp(*amplitude_scale)
    except TypeCheckError:
        pass

    try:
        check_type(amplitude_scale, ScalarFloat)
        return pulse_name * qua.amp(amplitude_scale)
    except TypeCheckError:
        pass

    raise ValueError(f"Invalid amplitude scale: {amplitude_scale}")
