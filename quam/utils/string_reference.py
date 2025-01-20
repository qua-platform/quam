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


def split_reference(string: str) -> Tuple[str, str]:
    """Split a string reference into its parent reference and attribute

    Args:
        string: The reference string

    Returns:
        A tuple containing the parent reference string and the attribute

    Raises:
        ValueError: If the string is not a valid reference
        ValueError: If the string equals "#/"

    Examples:
        split_reference("#/a/b/c") == ("#/a/b", "c")
        split_reference("#/a/b") == ("#/a", "b")
        split_reference("#/a") == ("#/", "a")
    """
    if not is_reference(string):
        raise ValueError(f"String {string} is not a reference")
    if string == "#/":
        raise ValueError(f"String {string} has no parent")
    if string == "#./":
        return "#../", ""
    if string == "#../":
        return "#../../", ""

    parent_reference, attr = string.rsplit("/", 1)
    if parent_reference in ("#", "#.", "#.."):
        parent_reference += "/"
    return parent_reference, attr


def join_references(base, relative):
    """Joins a base reference with another relative reference

    Args:
        base: The base reference, either absolute ("#/") or relative ("#./" or "#../")
        relative: The relative reference ("#./" or "#../")

    Returns:
        The joined reference

    Disallows:
      - Joining an absolute relative path ('#/...') with any base
        (raises ValueError).
      - Navigating above the root of an absolute base (#/...)
        (raises ValueError).

    Examples:
        join_references("#/a/b/c", "#./d/e/f") == "#/a/b/c/d/e/f"
        join_references("#/a/b/c", "#../d/e/f") == "#/a/b/d/e/f"
    """
    # Disallow if 'relative' starts with "#/" (i.e., an absolute path)
    if relative.startswith("#/"):
        raise ValueError(
            "Cannot join an absolute reference path with another absolute path"
            f"base reference: {base}, relative reference: {relative}"
        )

    # Split the base and relative references into segments (dropping the '#' prefix)
    base_segments = base[1:].split("/")
    relative_segments = relative[1:].split("/")

    # Check if the base is absolute: '#/...' => first segment == ""
    is_absolute = base_segments and base_segments[0] == ""

    # Process each segment from the relative path
    for seg in relative_segments:
        if seg == ".":
            # "current directory": do nothing
            continue
        elif seg == "..":
            _handle_go_up(base_segments, is_absolute)
        else:
            # Normal segment: just append
            base_segments.append(seg)

    # Reassemble and return
    return "#" + "/".join(base_segments)


def _handle_go_up(base_segments, is_absolute):
    """Handles a ".." (parent directory) segment, modifying base_segments in place.

    - If base is absolute, never allow popping the empty root segment [""].
    - If base is relative, allow accumulating ".." if there's nowhere left to pop.
    - Special rule: if the last segment is ".", replace it with ".." (to handle
      cases like #./a + #../../b => #../b).
    """
    if is_absolute:
        # For an absolute base (e.g. ["", "a", "b"]), we don't let it go above #/
        # The first segment is always "", so we only pop if len > 1
        if len(base_segments) > 1:
            base_segments.pop()
        else:
            raise ValueError("Cannot navigate above the root")
    else:
        # For a relative base, we can accumulate ".."
        if not base_segments:
            # Nothing to pop, just accumulate an additional ".."
            base_segments.append("..")
        else:
            last = base_segments[-1]
            if last == ".":
                # Replace '.' with '..'
                base_segments[-1] = ".."
            elif last == "..":
                # Already '..', add one more level
                base_segments.append("..")
            else:
                # Normal directory name, pop it
                base_segments.pop()
