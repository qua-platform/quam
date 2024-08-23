from typing import Tuple, Any
from collections import UserList, UserDict


DELIMITER = "."


def is_reference(string: str) -> bool:
    """Check if a string is a reference,

    A reference should be a string that starts with "#/", "#./" or "#../"
    """
    if not isinstance(string, str):
        return False
    return string.startswith(("#/", "#./", "#../"))


def is_absolute_reference(string: str) -> bool:
    """Check if a string is an absolute reference

    A relative reference starts with "#./" or "#../"
    An absolute reference starts with ":" but is not followed by "./" or "../"
    """
    if not is_reference(string):
        return False
    return string.startswith("#/")


def split_next_attribute(string: str, splitter: str = "/") -> Tuple[str, str]:
    """Get the next attribute of a reference string, i.e. until a splitter (default: /)

    Args:
        string: string to split
        splitter:  splitter to split the string at (default: "/")
    Returns:
        A tuple consisting of:
        - A string of the next attribute, i.e. until the first splitter
        - The remaining string from the first splitter
    """
    string = string.lstrip("#/")

    if not len(string):
        return "", ""

    if splitter in string:
        return tuple(string.split(splitter, 1))

    return string, ""


def get_relative_reference_value(obj, string: str) -> Any:
    """Get the value of a reference string relative to an object

    Performs recursive calls to get the value of nested references

    Args:
        string: The reference string

    Returns:
        The value of the reference string relative to the object

    Raises:
        AttributeError: If the object does not have the attribute
    """
    string = string.lstrip("#/")

    if not string:
        return obj
    if string.startswith("../"):
        return get_relative_reference_value(obj.parent, string[3:])
    elif string.startswith("./"):
        return get_relative_reference_value(obj, string[2:])

    next_attr, remaining_string = split_next_attribute(string)

    if next_attr.isdigit() and isinstance(obj, (list, UserList)):
        try:
            obj_attr = obj[int(next_attr)]
        except KeyError as e:
            raise AttributeError(f"Object {obj} has no attribute {next_attr}") from e
    elif isinstance(obj, (dict, UserDict)):
        if next_attr in obj:
            obj_attr = obj[next_attr]
        elif next_attr.isdigit() and int(next_attr) in obj:
            obj_attr = obj[int(next_attr)]
        else:
            raise AttributeError(f"Object {obj} has no attribute {next_attr}")
    else:
        obj_attr = getattr(obj, next_attr)

    return get_relative_reference_value(obj_attr, remaining_string)


def get_referenced_value(obj, string: str, root=None) -> Any:
    """Get the value of a reference string

    A string reference is a string that starts with "#/", "#./" or "#../".
    See documentation for details.

    Args:
        string: The reference string
        root: The root object to start the search from (default: None)
            Only relevant if the string is an absolute reference.

    Returns:
        The value that the reference string points to

    Raises:
        ValueError: If the string is not a valid reference
    """
    if not is_reference(string):
        raise ValueError(f"String {string} is not a reference")

    if is_absolute_reference(string):
        obj = root

    try:
        return get_relative_reference_value(obj, string)
    except (AttributeError, KeyError) as e:
        raise ValueError(f"String {string} is not a valid reference, Error: {e}") from e
