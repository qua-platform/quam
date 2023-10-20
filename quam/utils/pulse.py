from typing import Tuple


__all__ = ["pulse_str_to_axis_axis_angle"]


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
