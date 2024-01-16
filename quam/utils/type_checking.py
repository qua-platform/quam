from typing import Union

__all__ = ["type_is_optional"]


def type_is_optional(type_) -> bool:
    """Check if a type is Optional[T] for some type T.

    Args:
        type_: The type to check.

    Returns:
        True if the type is Optional[T] for some type T, False otherwise.

    Notes:
        This function does not check if the type is a Union of None and some other
        type, only if it is a Union of exactly two types, one of which is None.
        So Optional[Union[str, int]] will return False, but Optional[str] will return
        True.
    """
    if not hasattr(type_, "__origin__"):
        return False
    if type_.__origin__ is not Union:
        return False
    if len(type_.__args__) != 2:
        return False
    if type_.__args__[1] is not type(None):
        return False
    return True
