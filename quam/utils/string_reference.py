from typing import Tuple, Any
from collections import UserList, UserDict

from quam.utils.exceptions import InvalidReferenceError

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
        ValueError: If the string is not a valid reference format, i.e. doesn't start
            correctly.
        InvalidReferenceError: If the reference format is valid but the path cannot be
            resolved.
    """
    if not is_reference(string):
        # Keep ValueError for format issues
        raise ValueError(
            f"String {string} is not a reference format. "
            "It should start with '#/', '#./' or '#../'"
        )

    if is_absolute_reference(string):
        obj = root

    try:
        return get_relative_reference_value(obj, string)
    except (AttributeError, KeyError) as e:
        # Raise the specific error here, chaining the original exception
        msg = f"Could not resolve reference '{string}'"
        raise InvalidReferenceError(msg) from e


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
    """
    Joins a base reference (absolute '#/something...' or relative '#./...', '#../...')
    with another relative reference ('#./...', '#../...', etc.).

    Disallows:
      - Joining an absolute relative path ('#/...') with any base (raises ValueError).
      - Navigating above the root of an absolute base (#/...) (raises ValueError).

    For an absolute base (e.g. '#/a/b'):
        - If we end up with a trailing slash (like '#/a/'), we remove it,
          unless it's the root path '#/'.

    For a relative base (e.g. '#./a/b'):
        - We allow accumulating extra '..' if we pop everything (no "true root").
        - We don't remove trailing slashes for relative references (e.g. '#../' remains '#../').
    """
    # 1) Disallow if 'relative' starts with "#/" (i.e., another absolute path)
    if relative.startswith("#/"):
        raise ValueError("Cannot join an absolute path with another absolute path")

    # Determine if base is absolute (#/...)
    is_absolute = base.startswith("#/")

    # 2) Split the base and relative references (dropping the '#' prefix)
    base_segments = [""] if base == "#/" else base[1:].split("/")
    relative_segments = relative[1:].split("/")

    # 3) Process each segment from the relative path
    for seg in relative_segments:
        if seg in [".", ""]:
            # "current directory": do nothing
            continue
        elif seg == "..":
            _handle_go_up(base_segments, is_absolute)
        else:
            # Normal segment: just append
            base_segments.append(seg)

    # Remove empty segments
    base_segments = [seg for seg in base_segments if seg != ""]

    # Reassemble and return
    if is_absolute:
        return "#/" + "/".join(base_segments)
    else:
        return "#" + "/".join(base_segments)


def _handle_go_up(base_segments, is_absolute):
    """
    Handles a ".." (parent directory) segment, modifying base_segments in place.
      - If base is absolute, never allow popping the root (the first empty segment).
      - If base is relative, we allow accumulating '..' if there's nowhere left to pop.
      - Special rule: if the last segment is '.', replace it with '..'.
    """
    if is_absolute:
        # For an absolute base: if len>1, we can pop beyond the root's empty segment
        if len(base_segments) > 1:
            base_segments.pop()
        else:
            raise ValueError("Cannot navigate above the root")
    else:
        # For a relative base, we can accumulate '..'
        if not base_segments:
            # Nothing to pop => just add '..'
            base_segments.append("..")
        else:
            last = base_segments[-1]
            if last == ".":
                # Replace '.' with '..'
                base_segments[-1] = ".."
            elif last == "..":
                # Already '..', just add another '..'
                base_segments.append("..")
            else:
                # It's a normal directory (e.g. 'a'), so pop it
                base_segments.pop()
