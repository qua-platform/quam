from typing import Sequence, Tuple, Any


def is_reference(string: str) -> bool:
    """Check if a string is a reference, i.e. a string that starts with a colon"""
    if not isinstance(string, str):
        return False
    if not string.startswith(":"):
        return False
    return True


def is_absolute_reference(string: str) -> bool:
    """Check if a string is an absolute reference

    A relative reference starts with ":./" or ":../"
    An absolute reference starts with ":" but is not followed by "./" or "../"
    """
    if not is_reference(string):
        return False
    if string.startswith(":."):
        return False
    return True


def split_next_attribute(
    string: str, splitters: Sequence[str] = ".["
) -> Tuple[str, str]:
    """Get the next attribute of a reference string, i.e. until a splitter

    A splitter is usually either a dot or an opening square bracket

    Args:
        string: string to split
        splitters: a sequence of characters to split on, e.g. "." and "["

    Returns:
        A tuple consisting of:
        - A string of the next attribute, i.e. until the first splitter
        - The remaining string from the first splitter
    """
    # Determine the next splitter, either a dot or square brackets []
    splitter_idxs = {}
    for splitter in splitters:
        try:
            splitter_idxs[splitter] = string.index(splitter)
        except ValueError:
            splitter_idxs[splitter] = None

    if set(splitter_idxs.values()) == {None}:
        return string, ""

    next_splitter = min(key for key, val in splitter_idxs.items() if val is not None)
    splitter_idx = splitter_idxs[next_splitter]
    return string[:splitter_idx], string[splitter_idx:]


def get_relative_reference_value(obj, string: str) -> Any:
    """Get the value of a reference string relative to an object

    Performs recursive calls to get the value of nested references
    """
    string = string.lstrip(":")

    if not string:
        return obj
    if string.startswith("../"):
        return get_relative_reference_value(obj.parent, string[3:])
    elif string.startswith("./"):
        return get_relative_reference_value(obj, string[2:])
    elif string.startswith("["):
        close_idx = string.index("]")
        key = string[1:close_idx]
        key = key.lstrip("'\"").rstrip("'\"")
        return get_relative_reference_value(obj[key], string[close_idx + 1 :])
    elif string.startswith("."):
        string = string[1:]

    next_attr, remaining_string = split_next_attribute(string)

    return get_relative_reference_value(getattr(obj, next_attr), remaining_string)


def get_referenced_value(obj, string: str, root=None) -> Any:
    if not is_reference(string):
        raise ValueError(f"String {string} is not a reference")

    if is_absolute_reference(string):
        obj = root

    try:
        return get_relative_reference_value(obj, string)
    except (AttributeError, KeyError):
        raise ValueError(f"String {string} is not a valid reference")
