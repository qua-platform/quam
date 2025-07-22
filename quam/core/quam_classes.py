from __future__ import annotations
from collections.abc import Iterable
import sys
import warnings
from pathlib import Path
from copy import deepcopy
from typing import (
    Iterator,
    Union,
    Generator,
    ClassVar,
    Any,
    List,
    Dict,
    Sequence,
    TypeVar,
    get_type_hints,
    get_origin,
    get_args,
    Optional,
)
from functools import partial
from dataclasses import dataclass, fields, is_dataclass, MISSING
from collections import UserDict, UserList

from quam.serialisation import AbstractSerialiser, JSONSerialiser
from quam.utils import (
    get_dataclass_attr_annotations,
    ReferenceClass,
    string_reference,
    get_full_class_path,
    type_is_optional,
    generate_config_final_actions,
)
from quam.core.quam_instantiation import instantiate_quam_class
from quam.config import get_quam_config
from quam.utils.exceptions import InvalidReferenceError

from .qua_config_template import qua_config_template

from qm.type_hinting import DictQuaConfig

__all__ = [
    "QuamBase",
    "QuamRoot",
    "QuamComponent",
    "QuamDict",
    "QuamList",
    "quam_dataclass",
]


def _get_value_annotation(cls_or_obj: Union[type, object], attr: str) -> Optional[type]:
    """Get the type annotation for the values in a QuamDict or QuamList.

    If the QuamDict is defined as Dict[str, int], this will return int.
    If the QuamList is defined as List[int], this will return int.
    In all other cases, this will return None.
    """
    if cls_or_obj is None or attr is None:
        return None

    cls = cls_or_obj if isinstance(cls_or_obj, type) else cls_or_obj.__class__

    annotated_attrs = get_type_hints(cls)
    if attr not in annotated_attrs:
        return None

    attr_annotation = annotated_attrs[attr]
    origin = get_origin(attr_annotation)
    if origin == dict:
        return get_args(attr_annotation)[1]
    elif origin == list:
        return get_args(attr_annotation)[0]
    return None


def convert_dict_and_list(value, cls_or_obj=None, attr=None):
    """Convert a dict or list to a QuamDict or QuamList if possible."""
    if isinstance(value, dict):
        value_annotation = _get_value_annotation(cls_or_obj=cls_or_obj, attr=attr)
        return QuamDict(value, value_annotation=value_annotation)
    elif type(value) == list:
        value_annotation = _get_value_annotation(cls_or_obj=cls_or_obj, attr=attr)
        return QuamList(value, value_annotation=value_annotation)
    else:
        return value


def sort_quam_components(
    components: List["QuamComponent"], max_attempts=5
) -> List["QuamComponent"]:
    """Sort QuamComponent objects based on their config_settings.

    Args:
        components: A list of QuamComponent objects.
        max_attempts: The maximum number of attempts to sort the components.
            If the components aren't yet properly sorted after all these attempts,
            a warning is raised and the components are returned in the final attempted
            ordering.

    Returns:
        A sorted list of QuamComponent objects.

    Note:
        This function is used by
        [`QuamRoot.generate_config`][quam.core.quam_classes.QuamRoot.generate_config]
        to determine the order in which to add the components to the QUA config.
        This sorting isn't guaranteed to be successful.
    """
    sorted_components = components.copy()
    for _ in range(max_attempts):
        adjustments_made = False

        for component in components:
            if component.config_settings is None:
                continue

            component_idx = sorted_components.index(component)

            if "after" in component.config_settings:
                for after_component in component.config_settings["after"]:
                    after_component_idx = sorted_components.index(after_component)
                    if after_component_idx < component_idx:
                        continue
                    sorted_components.remove(after_component)
                    sorted_components.insert(component_idx, after_component)
                    adjustments_made = True

            if "before" in component.config_settings:
                for before_component in component.config_settings["before"]:
                    before_component_idx = sorted_components.index(before_component)
                    if before_component_idx > component_idx:
                        continue
                    sorted_components.remove(before_component)
                    sorted_components.insert(component_idx + 1, before_component)
                    adjustments_made = True

        if not adjustments_made:
            break
    else:
        warnings.warn(
            "Unable to sort QuamComponents based on config_settings. "
            "This may cause issues when generating the QUA config."
        )

    return sorted_components


def _quam_dataclass(cls=None, **kwargs):
    """Dataclass for QUAM classes.

    This class is used as a patch to maintain compatibility with Python 3.9, as
    these do not support the dataclass argument `kw_only`. This argument is needed to
    ensure inheritance of parent dataclasses is allowed.

    Args:
    - cls: The QUAM class to decorate.
    - kwargs: The arguments to pass to the dataclass decorator.
      By default, kw_only=True and eq=False are passed, though they can be overwritten.
    Notes:
    - This custom dataclass is no longer necessary once Python 3.9 support is dropped
    - The actual custom dataclass is `quam_dataclass` (without the underscore). This
      function is only used to trick type checkers into recognizing it as a dataclass.
    - From Python 3.10 onwards, this customized dataclass is no longer needed, as then
      the following two decorators are equivalent:
      - @quam_dataclass
      - @dataclass(eq=False, kw_only=True)
    """
    if cls is None:
        return partial(_quam_dataclass, **kwargs)

    kwargs.setdefault("kw_only", True)
    kwargs.setdefault("eq", False)

    if sys.version_info.minor > 9:
        return dataclass(cls, **kwargs)

    from quam.utils.dataclass import _quam_patched_dataclass

    return _quam_patched_dataclass(cls, **kwargs)


# Exec statement is needed to trick type checkers into recognizing it as a dataclass
# This will no longer be necessary once we drop support for Python 3.9
quam_dataclass = dataclass
exec("quam_dataclass = _quam_dataclass")


class ParentDescriptor:
    """Descriptor for the parent attribute of QuamBase.

    This descriptor is used to ensure that the parent attribute of a QuamBase
    object is not overwritten. This is to prevent the following situation:

    ```
    parent1 = QuamBase()
    parent2 = QuamBase()

    child = QuamBase()
    child.parent = parent1  # This is fine
    child.parent = parent2  # This raises an AttributeError
    ```
    """

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if "parent" in instance.__dict__:
            return instance.__dict__["parent"]
        return None

    def __set__(self, instance, value):
        if value is None:
            instance.__dict__.pop("parent", None)
            return

        if "parent" in instance.__dict__ and instance.__dict__["parent"] is not value:
            cls = instance.__class__.__name__
            raise AttributeError(
                f"Cannot overwrite parent attribute of {cls}. "
                f"To modify {cls}.parent, first set {cls}.parent = None"
            )
        instance.__dict__["parent"] = value


class QuamBase(ReferenceClass):
    """Base class for any QUAM component class.

    args:
        parent: The parent of this object. This is automatically set when adding
            this object to another QuamBase object.
        config_settings: A dictionary of configuration settings for this object.
            This is used by [`QuamRoot.generate_config`][quam.core.quam_classes.QuamRoot.generate_config]
            to determine the order in which to add the components to the QUA config.
            Keys are "before" and "after", and the values are a list of QuamComponents

    Note:
        This class should not be used directly, but should generally be subclassed.
        The subclasses should be dataclasses.
    """

    parent: ClassVar["QuamBase"] = ParentDescriptor()
    _last_instantiated_root: ClassVar[Optional["QuamRoot"]] = None
    config_settings: ClassVar[Dict[str, Any]] = None

    def __init__(self):
        # This prohibits instantiating without it being a dataclass
        # This means that we have to subclass this class and make it a dataclass
        if not is_dataclass(self):
            if type(self) in [QuamBase, QuamComponent, QuamRoot]:
                raise TypeError(
                    f"Cannot instantiate {self.__class__.__name__} directly. "
                    "Please create a subclass and make it a dataclass."
                )
            else:
                raise TypeError(
                    f"Cannot instantiate {self.__class__.__name__}. "
                    "Please make it a dataclass."
                )

    def _get_attr_names(self) -> List[str]:
        """Get names of all dataclass attributes of this object.

        Returns:
            List of attribute names.

        Raises:
            AssertionError if not a dataclass.
        """
        assert is_dataclass(self)
        return [data_field.name for data_field in fields(self)]

    def get_root(self) -> Optional[QuamRoot]:
        """Get the QuamRoot object of this object.

        This function recursively searches the parent chain for a QuamRoot object.
        If no QuamRoot object is found, it will return the last instantiated QuamRoot
        if it exists, else None.

        Returns:
            The root of this object, or None if no root is found.
        """
        if self.parent is not None:
            return self.parent.get_root()

        if self._last_instantiated_root is not None:
            warnings.warn(
                f"This component is not part of any QuamRoot, using last "
                f"instantiated QuamRoot. This is not recommended as it may lead to "
                f"unexpected behaviour. Component: {self.__class__.__name__}"
            )
            return self._last_instantiated_root
        return None

    def get_attr_name(self, attr_val: Any) -> str:
        """Get the name of an attribute that matches the value.

        Args:
            attr_val: The value of the attribute.

        Returns:
            The name of the attribute.

        Raises:
            AttributeError if not found.
        """
        for attr_name in self._get_attr_names():
            if self.get_raw_value(attr_name) is attr_val:
                return attr_name
        else:
            raise AttributeError(
                "Could not find name corresponding to attribute.\n"
                f"attribute: {attr_val}\n"
                f"obj: {self}"
            )

    def _attr_val_is_default(self, attr: str, val: Any) -> bool:
        """Check whether the value of an attribute is the default value.

        Args:
            attr: The name of the attribute.
            val: The value of the attribute.

        Returns:
            True if the value is the default value, False otherwise.
            False is also returned if the parent is not a dataclass
        """
        if not is_dataclass(self):
            return False

        dataclass_fields = fields(self)
        if not any(field.name == attr for field in dataclass_fields):
            return False

        field = next(field for field in dataclass_fields if field.name == attr)
        if field.default is not MISSING:
            return val == field.default
        elif field.default_factory is not MISSING:
            try:
                default_val = field.default_factory()
                return val == default_val
            except TypeError:
                return False

        return False

    @classmethod
    def _val_matches_attr_annotation(cls, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        The attribute type must exactly match the annotation.
        For dict and list, no additional type check of args is performed.
        """
        annotated_attrs = get_dataclass_attr_annotations(cls)
        if attr not in annotated_attrs["allowed"]:
            return False

        required_type = annotated_attrs["allowed"][attr]
        if type_is_optional(required_type):
            required_type = get_args(required_type)[0]

        if required_type == dict or get_origin(required_type) == dict:
            return isinstance(val, (dict, QuamDict))
        elif required_type == list or get_origin(required_type) == list:
            return isinstance(val, (list, QuamList))
        return type(val) == required_type

    def get_reference(
        self, attr: Optional[str] = None, relative_path: Optional[str] = None
    ) -> Optional[str]:
        """Get the reference path of this object.

        Args:
            attr: The optional attribute to get the reference path for.
                If None, the reference path of the object itself is returned.
            relative_path: The optional relative path to join with the reference path.

        Returns:
            The reference path of this object.

        Examples:
            We assume a QuamRoot object with a component "elem".
            - elem.get_reference() == "#/elem"
            - elem.get_reference(attr="child") == "#/elem/child"
            - elem.get_reference(relative_path="#./child") == "#/elem/child"
            - elem.get_reference(relative_path="#../child") == "#/child"
            - elem.get_reference(relative_path="#./child/grandchild") == "#/elem/child/grandchild"
        """

        if attr is not None and relative_path is not None:
            raise ValueError(
                "Cannot specify both attr and relative_path. "
                "Please specify only one of them."
            )

        if self.parent is None:
            raise AttributeError(
                "Unable to extract reference path for {self}: No parent defined"
            )

        try:
            base_reference = self.parent.get_reference()
            if base_reference == "#/":
                base_reference = "#"
        except AttributeError:
            raise AttributeError(
                f"Unable to extract reference path for {self}: Could not get "
                f"reference path for parent {self.parent}"
            )

        try:
            attr_name = self.parent.get_attr_name(self)
        except AttributeError:
            raise AttributeError(
                f"Unable to extract reference path for {self}: Could not get "
                f"attribute name from parent {self.parent}"
            )

        reference = f"{base_reference}/{attr_name}"

        if relative_path is not None:
            if not string_reference.is_reference(relative_path):
                raise ValueError(
                    f"Unable to extract reference path for {self}: "
                    f"relative_path {relative_path} is not a reference"
                )

            reference = string_reference.join_references(reference, relative_path)
        elif attr is not None:
            reference = f"{reference}/{attr}"

        return reference

    def get_attrs(
        self, follow_references: bool = False, include_defaults: bool = True
    ) -> Dict[str, Any]:
        """Get all attributes and corresponding values of this object.

        Args:
            follow_references: Whether to follow references when getting the value.
                If False, the reference will be returned as a string.
            include_defaults: Whether to include attributes that have the default
                value.

        Returns:
            A dictionary of attribute names and values.

        """
        attr_names = self._get_attr_names()

        skip_attrs = getattr(self, "_skip_attrs", [])
        attr_names = [attr for attr in attr_names if attr not in skip_attrs]

        if not follow_references:
            attrs = {attr: self.get_raw_value(attr) for attr in attr_names}
        else:
            attrs = {attr: getattr(self, attr) for attr in attr_names}

        if not include_defaults:
            attrs = {
                attr: val
                for attr, val in attrs.items()
                if not self._attr_val_is_default(attr, val)
            }
        return attrs

    def to_dict(
        self, follow_references: bool = False, include_defaults: bool = False
    ) -> Dict[str, Any]:
        """Convert this object to a dictionary.

        Args:
            follow_references: Whether to follow references when getting the value.
                If False, the reference will be returned as a string.
            include_defaults: Whether to include attributes that have the default

        Returns:
            A dictionary representation of this object.
            Any QuamBase objects will be recursively converted to dictionaries.

        Note:
            If the value of an attribute does not match the annotation, the
            `"__class__"` key will be added to the dictionary. This is to ensure
            that the object can be reconstructed when loading from a file.
        """
        attrs = self.get_attrs(
            follow_references=follow_references, include_defaults=include_defaults
        )
        quam_dict = {}
        for attr, val in attrs.items():
            if isinstance(val, QuamBase):
                quam_dict[attr] = val.to_dict(
                    follow_references=follow_references,
                    include_defaults=include_defaults,
                )
            else:
                quam_dict[attr] = val

        # Add __class__ to specify the class of the object
        quam_dict["__class__"] = get_full_class_path(self)

        return quam_dict

    def iterate_components(
        self, skip_elems: Optional[Sequence["QuamBase"]] = None
    ) -> Generator["QuamBase", None, None]:
        """Iterate over all QuamBase objects in this object, including nested objects.

        Args:
            skip_elems: A sequence of QuamBase objects to skip.
                This is used to prevent infinite loops when iterating over nested
                objects.

        Returns:
            A generator of QuamBase objects.
        """
        if skip_elems is None:
            skip_elems = []

        # We don't use "self in skip_elems" because we want to check for identity,
        # not equality. The reason is that you would otherwise have to instantiate
        # dataclasses using @dataclass(eq=False)
        in_skip_elems = any(self is elem for elem in skip_elems)
        if isinstance(self, QuamComponent) and not in_skip_elems:
            skip_elems.append(self)
            yield self

        attrs = self.get_attrs(follow_references=False, include_defaults=True)

        for attr_val in attrs.values():
            if any(attr_val is elem for elem in skip_elems):
                continue

            if isinstance(attr_val, QuamBase):
                yield from attr_val.iterate_components(skip_elems=skip_elems)

    def _is_reference(self, attr: str) -> bool:
        """Check whether an attribute is a reference.

        Args:
            attr: The name of the attribute.

        Returns:
            True if the attribute is a reference, False otherwise.

        Note:
            This function is used from the ReferenceClass class.
        """
        return string_reference.is_reference(attr)

    def _get_referenced_value(self, reference: str) -> Any:
        """Get the value of an attribute by reference

        Args:
            reference: The reference to the attribute.

        Returns:
            The value of the attribute, or the reference if it is not a reference

        Note:
            This function is used from the ReferenceClass class.
        """
        if not string_reference.is_reference(reference):
            return reference

        root = self.get_root()
        if string_reference.is_absolute_reference(reference) and root is None:
            warnings.warn(
                f"No QuamRoot initialized, cannot retrieve absolute reference "
                f"{reference} from {self.__class__.__name__}"
            )
            return reference

        try:
            return string_reference.get_referenced_value(self, reference, root=root)
        except InvalidReferenceError as e:
            try:
                ref = f"{self.__class__.__name__}: {self.get_reference()}"
            except Exception:
                ref = self.__class__.__name__

            # Construct message using the chained exception's message
            base_error_msg = str(e)
            component_ref_str = f"component {ref}"
            msg = (
                f'Could not get reference "{reference}" from {component_ref_str}. '
                f"Error: {base_error_msg}"
            )

            try:
                cfg = get_quam_config()
                raise_error_missing_reference = cfg.raise_error_missing_reference
            except FileNotFoundError:
                # Default behavior if config file not found
                raise_error_missing_reference = False

            if not raise_error_missing_reference:
                warnings.warn(msg)
            else:
                # Re-raise with context, keeping the original exception chain
                raise InvalidReferenceError(msg) from e
            return reference

    def print_summary(self, indent: int = 0):
        """Print a summary of the QuamBase object.

        Args:
            indent: The number of spaces to indent the summary.
        """
        if self.get_root() is self:
            full_name = "QUAM:"
        elif self.parent is None:
            full_name = f"{self.__class__.__name__} (parent unknown):"
        else:
            try:
                attr_name = self.parent.get_attr_name(self)
                full_name = f"{attr_name}: {self.__class__.__name__}"
            except AttributeError:
                full_name = f"{self.__class__.__name__}:"

        if not self.get_attrs():
            print(" " * indent + f"{full_name} Empty")
            return

        print(" " * indent + f"{full_name}")
        for attr, val in self.get_attrs().items():
            if isinstance(val, str):
                val = f'"{val}"'
            if isinstance(val, QuamBase):
                val.print_summary(indent=indent + 2)
            else:
                print(" " * (indent + 2) + f"{attr}: {val}")

    def set_at_reference(
        self, attr: str, value: Any, allow_non_reference: bool = False
    ):
        """Follow the reference of an attribute and set the value at the reference

        Args:
            attr: The attribute to set the value at the reference of.
            value: The value to set.
            allow_non_reference: Whether to allow the attribute to be a non-reference.
                If False, the attribute must be a reference or an error is raised.

        Raises:
            ValueError: If the attribute is not a reference and `allow_non_reference` is
                False.
            ValueError: If the reference is invalid, e.g. "#./" since it has no
                attribute.
        """
        raw_value = self.get_raw_value(attr)
        if not string_reference.is_reference(raw_value):
            if not allow_non_reference:
                raise ValueError(
                    f"Cannot set at reference because attr '{attr}' is not a reference. "
                    f"'{attr}' = {raw_value}"
                )
            else:
                setattr(self, attr, value)
                return

        parent_reference, ref_attr = string_reference.split_reference(raw_value)
        if not ref_attr:
            raise ValueError(
                f"Unsuccessful attempt to set the value at reference {raw_value} for "
                f"attribute {attr} because the reference is invalid as it has no "
                "attribute"
            )

        parent_obj = self._get_referenced_value(parent_reference)
        raw_referenced_value = parent_obj.get_raw_value(ref_attr)
        if string_reference.is_reference(raw_referenced_value) and isinstance(
            parent_obj, QuamBase
        ):
            parent_obj.set_at_reference(ref_attr, value)
        else:
            setattr(parent_obj, ref_attr, value)


# Type annotation for QuamRoot, can be replaced by typing.Self from Python 3.11
QuamRootType = TypeVar("QuamRootType", bound="QuamRoot")


class QuamRoot(QuamBase):
    """Base class for the root of a QUAM object.

    This class should be subclassed and made a dataclass.

    Note:
        This class should not be used directly, but should generally be subclassed and
        made a dataclass. The dataclass fields should correspond to the QUAM root
        structure.
    """

    def __post_init__(self):
        QuamBase._last_instantiated_root = self
        self.serialiser = self.get_serialiser()
        super().__post_init__()

    def __setattr__(self, name, value):
        converted_val = convert_dict_and_list(value, cls_or_obj=self, attr=name)
        super().__setattr__(name, converted_val)

        if isinstance(converted_val, QuamBase) and name != "parent":
            converted_val.parent = self

    @classmethod
    def get_serialiser(cls) -> AbstractSerialiser:
        """Get the serialiser for the QuamRoot class, which is the JSONSerialiser.

        This method can be overridden by subclasses to provide a custom serialiser.
        """
        return JSONSerialiser()

    def get_reference(
        self, attr: Optional[str] = None, relative_path: Optional[str] = None
    ) -> Optional[str]:
        if attr is not None:
            return f"#/{attr}"

        reference = "#/"
        if relative_path is not None:
            reference = string_reference.join_references(reference, relative_path)
        return reference

    def get_root(self: QuamRootType) -> QuamRootType:
        """Get the QuamRoot object of this object, i.e. the object itself.

        This QuamRoot function overrides the QuamBase function to return the object
        itself, rather than following the parent chain.

        Returns:
            The current QuamRoot object (self).
        """
        return self

    def save(
        self,
        path: Optional[Union[Path, str]] = None,
        content_mapping: Optional[Dict[str, str]] = None,
        include_defaults: bool = False,
        ignore: Optional[Sequence[str]] = None,
    ):
        """Save the entire QuamRoot object to a file. This includes nested objects.

        Args:
            path: The path to save the file to. If None, the path will be extracted from
                the `state_path` attribute of the serialiser, which could be set by the
                quam config file or environment variable.
            content_mapping: Optional mapping of component names to filenames. This can
                be used to save different parts of the QuamRoot object to different
                files.
            include_defaults: Whether to include attributes that have the default
                value.
            ignore: A list of components to ignore.
        """
        self.serialiser.save(
            quam_obj=self,
            path=path,
            content_mapping=content_mapping,
            include_defaults=include_defaults,
            ignore=ignore,
        )

    @classmethod
    def load(
        cls: type[QuamRootType],
        filepath_or_dict: Optional[Union[str, Path, dict]] = None,
        validate_type: bool = True,
        fix_attrs: bool = True,
    ) -> QuamRootType:
        """Load a QuamRoot object from a file.

        Args:
            filepath_or_dict: The path to the file/folder to load, or a dictionary.
                The dictionary would be the result from a call to `QuamRoot.save()`
                Can be omitted, in which case the serialiser will use the default state
                path, which is typically defined in the quam config file.
            validate_type: Whether to validate the type of all attributes while loading.
            fix_attrs: Whether attributes can be added to QuamBase objects that are not
                defined as dataclass fields.

        Returns:
            A QuamRoot object instantiated from the file/folder/dict.
        """
        if isinstance(filepath_or_dict, dict):
            contents = filepath_or_dict
        else:
            serialiser = cls.get_serialiser()
            contents, _ = serialiser.load(filepath_or_dict)

        return instantiate_quam_class(
            quam_class=cls,
            contents=contents,
            fix_attrs=fix_attrs,
            validate_type=validate_type,
        )

    def generate_config(self) -> DictQuaConfig:
        """Generate the QUA configuration from the QUAM object.

        Returns:
            A dictionary with the QUA configuration.

        Note:
            This function collects all the nested QuamComponent objects and calls
            `QuamComponent.apply_to_config` on them.
        """
        qua_config = deepcopy(qua_config_template)

        quam_components = list(self.iterate_components())
        sorted_components = sort_quam_components(quam_components)

        for quam_component in sorted_components:
            quam_component.apply_to_config(qua_config)

        generate_config_final_actions(qua_config)

        return qua_config


class QuamComponent(QuamBase):
    """Base class for any QUAM component class.

    Examples of QuamComponent classes are [`Mixer`][quam.components.hardware.Mixer],
    [`LocalOscillator`][quam.components.hardware.LocalOscillator],
    [`Pulse`][quam.components.pulses.Pulse], etc.

    Note:
        This class should be subclassed and made a dataclass.
    """

    def __setattr__(self, name, value):
        converted_val = convert_dict_and_list(value, cls_or_obj=self, attr=name)
        super().__setattr__(name, converted_val)

        if isinstance(converted_val, QuamBase) and name != "parent":
            converted_val.parent = self

    def apply_to_config(self, config: dict) -> None:
        """Add information to the QUA configuration, such as pulses and waveforms.

        Args:
            config: The QUA configuration dictionary. Initially this is a nearly empty
                dictionary, but

        Note:
            This function is called by
            [`QuamRoot.generate_config`][quam.core.quam_classes.QuamRoot.generate_config].

        Note:
            The config has a starting template, defined at [`quam.core.qua_config_template`][]
        """
        ...


@quam_dataclass
class QuamDict(UserDict, QuamBase):
    """A QUAM dictionary class.

    Any dict added to a `QuamBase` object is automatically converted to a `QuamDict`.
    The `QuamDict` adds the following functionalities to a dict:
    - Values can be references (see below)
    - Keys can also be accessed through attributes (e.g. `d.a` instead of `d["a"]`)

    # QuamDict references
    QuamDict values can be references, which are strings that start with `#`. See the
    documentation for details on references. An example is shown here:
    ```
    d = QuamDict({"a": 1, "b": "#./a"})
    assert d["b"] == 1
    ```

    Warning:
        This class is a subclass of `QuamBase`, but also of `UserDict`. As a result,
        it can be used as a normal dictionary, but it is not a subclass of `dict`.
    """

    _value_annotation: ClassVar[type] = None

    def __init__(self, dict=None, /, value_annotation: type = None, **kwargs):
        self.__dict__["data"] = {}
        self.__dict__["_value_annotation"] = value_annotation
        self.__dict__["_initialized"] = True
        super().__init__(dict, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            try:
                repr = f"{self.__class__.__name__}: {self.get_reference()}"
            except Exception:
                repr = self.__class__.__name__
            raise AttributeError(f'{repr} has no attribute "{key}"') from e

    def __setattr__(self, key, value):
        if key in ["data", "parent", "config_settings", "_initialized"]:
            super().__setattr__(key, value)
        else:
            self[key] = value

    def __getitem__(self, i):
        elem = super().__getitem__(i)
        if string_reference.is_reference(elem):
            try:
                elem = self._get_referenced_value(elem)
            except InvalidReferenceError as e:
                try:
                    repr = f"{self.__class__.__name__}: {self.get_reference()}"
                except Exception:
                    repr = self.__class__.__name__
                raise KeyError(
                    f"Could not get referenced value {elem} from {repr}"
                ) from e
        return elem

    # Overriding methods from UserDict
    def __setitem__(self, key, value):
        value = convert_dict_and_list(value)
        self._is_valid_setattr(key, value, error_on_False=True)
        super().__setitem__(key, value)

        if isinstance(value, QuamBase):
            value.parent = self

    def __eq__(self, other) -> bool:
        if isinstance(other, dict):
            return self.data == other
        return super().__eq__(other)

    def __repr__(self) -> str:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="^Could not get reference*",
                category=UserWarning,
            )
            return super().__repr__()

    # QUAM methods
    def _get_attr_names(self):
        return list(self.data.keys())

    def get_attrs(
        self, follow_references=False, include_defaults=True
    ) -> Dict[str, Any]:
        # TODO implement reference kwargs
        return self.data

    def get_attr_name(self, attr_val: Any) -> Union[str, int]:
        """Get the name of an attribute that matches the value.

        Args:
            attr_val: The value of the attribute.

        Returns:
            The name of the attribute. This can also be an int depending on the dict key

        Raises:
            AttributeError if not found.
        """
        for attr_name in self._get_attr_names():
            if attr_name in self and self.get_raw_value(attr_name) is attr_val:
                return attr_name
        else:
            raise AttributeError(
                "Could not find name corresponding to attribute.\n"
                f"attribute: {attr_val}\n"
                f"obj: {self}"
            )

    def _val_matches_attr_annotation(self, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        Called by [`QuamDict.to_dict`][quam.core.quam_classes.QuamDict.to_dict] to
        determine whether to add the __class__ key.

        Args:
            attr: The name of the attribute. Unused but added to match parent signature
            val: The value of the attribute.

        Note:
            The attribute val is compared to `QuamDict._value_annotation`, which is set
            when a dict is converted to a `QuamDict` using `convert_dict_and_list`.
        """
        if isinstance(val, (QuamDict, QuamList)):
            return True
        if self._value_annotation is None:
            return False
        return type(val) == self._value_annotation

    def _attr_val_is_default(self, attr: str, val: Any):
        """Check whether the value of an attribute is the default value.

        Overrides parent method.
        Since a QuamDict does not have any fixed attrs, this is always False.

        """
        return False

    def get_raw_value(self, attr: str) -> Any:
        """Get the value of an attribute without following references.

        Args:
            attr: The name of the attribute.

        Returns:
            The value of the attribute. If the value is a reference, it returns the
            reference string instead of the value it is referencing.
        """
        try:
            return self.__dict__["data"][attr]
        except KeyError as e:
            raise AttributeError(
                "Cannot get raw (unreferenced)value from attribute {attr} that does not"
                " exist in {self}"
            ) from e

    def iterate_components(
        self, skip_elems: Sequence[QuamBase] = None
    ) -> Generator["QuamBase", None, None]:
        """Iterate over all QuamBase objects in this object, including nested objects.

        Args:
            skip_elems: A sequence of QuamBase objects to skip.
                This is used to prevent infinite loops when iterating over nested
                objects.

        Returns:
            A generator of QuamBase objects.
        """
        if skip_elems is None:
            skip_elems = []

        for attr_val in self.data.values():
            if any(attr_val is elem for elem in skip_elems):
                continue

            if isinstance(attr_val, QuamBase):
                yield from attr_val.iterate_components(skip_elems=skip_elems)

    def to_dict(
        self, follow_references: bool = False, include_defaults: bool = False
    ) -> dict:
        """Convert this object to a dictionary.

        Ensures all child QUAM objects are also converted to dictionaries.

        Args:
            follow_references: Whether to follow references when getting the value.
                If False, the reference will be returned as a string.
            include_defaults: Whether to include attributes that have the default
                value.

        Returns:
            A dictionary representation of the object.
        """
        quam_dict = super().to_dict()

        # Remove __class__ from the dictionary as it's the default for a dict
        quam_dict.pop("__class__", None)

        return quam_dict


@quam_dataclass
class QuamList(UserList, QuamBase):
    """A QUAM list class.

    Any list added to a `QuamBase` object is automatically converted to a `QuamList`.
    The `QuamList` adds the following functionalities to a list:
    - Elements can be references (see below)

    # QuamList references
    QuamList values can be references, which are strings that start with `#`. See the
    documentation for details on references. An example is shown here:
    ```
    d = QuamList([1, "#./0"]])
    assert d[1] == 1
    ```

    Warning:
        This class is a subclass of `QuamBase`, but also of `UserList`. As a result,
        it can be used as a normal list, but it is not a subclass of `list`.
    """

    _value_annotation: ClassVar[type] = None

    def __init__(self, *args, value_annotation: type = None):
        self._value_annotation = value_annotation

        # We manually add elements using extend instead of passing to super()
        # To ensure that any dicts and lists get converted to QuamDict and QuamList
        super().__init__()
        if args:
            self.extend(*args)

    # Overloading methods from UserList
    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)

    def __repr__(self) -> str:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="^Could not get reference*",
                category=UserWarning,
            )
            return super().__repr__()

    def __getitem__(self, i):
        elem = super().__getitem__(i)
        if isinstance(i, slice):
            if isinstance(elem, QuamList):
                elem.parent = self.parent
            # This automatically gets the referenced values
            return list(elem)

        if string_reference.is_reference(elem):
            elem = self._get_referenced_value(elem)
        return elem

    def __setitem__(self, i, item):
        converted_item = convert_dict_and_list(item)
        super().__setitem__(i, converted_item)

        if isinstance(converted_item, QuamBase):
            converted_item.parent = self

    def __iadd__(self, other: Iterable):
        converted_other = [convert_dict_and_list(elem) for elem in other]
        return super().__iadd__(converted_other)

    def append(self, item: Any) -> None:
        converted_item = convert_dict_and_list(item)

        if isinstance(converted_item, QuamBase):
            converted_item.parent = self

        return super().append(converted_item)

    def insert(self, i: int, item: Any) -> None:
        converted_item = convert_dict_and_list(item)

        if isinstance(converted_item, QuamBase):
            converted_item.parent = self

        return super().insert(i, converted_item)

    def extend(self, iterable: Iterator) -> None:
        converted_iterable = [convert_dict_and_list(elem) for elem in iterable]
        for converted_item in converted_iterable:
            if isinstance(converted_item, QuamBase):
                converted_item.parent = self

        return super().extend(converted_iterable)

    # Quam methods
    def _val_matches_attr_annotation(self, attr: str, val: Any) -> bool:
        """Check whether the type of an attribute matches the annotation.

        Called by QuamList.to_dict to determine whether to add the __class__ key.
        For the QuamList, we compare the type to the _value_annotation.
        """
        if isinstance(val, (QuamDict, QuamList)):
            return True
        if self._value_annotation is None:
            return False
        return type(val) == self._value_annotation

    def get_attr_name(self, attr_val: Any) -> str:
        for k, elem in enumerate(self.data):
            if elem is attr_val:
                return str(k)
        else:
            raise AttributeError(
                "Could not find name corresponding to attribute"
                f"attribute: {attr_val}\n"
                f"obj: {self}"
            )

    def to_dict(
        self, follow_references: bool = False, include_defaults: bool = False
    ) -> list:
        """Convert this object to a list, usually as part of a dictionary representation.

        Args:
            follow_references: Whether to follow references when getting the value.
                If False, the reference will be returned as a string.
            include_defaults: Whether to include attributes that have the default
                value.

        Returns:
            A list with the values of this object. Any QuamBase objects will be
            recursively converted to dictionaries.

        Note:
            If the value of an attribute does not match the annotation of
            `QuamList._value_annotation`, the `"__class__"` key will be added to the
            dictionary. This is to ensure that the object can be reconstructed when
            loading from a file.
        """
        quam_list = []
        for val in self.data:
            if isinstance(val, QuamBase):
                quam_list.append(
                    val.to_dict(
                        follow_references=follow_references,
                        include_defaults=include_defaults,
                    )
                )
            else:
                quam_list.append(val)
        return quam_list

    def iterate_components(
        self, skip_elems: List[QuamBase] = None
    ) -> Generator["QuamBase", None, None]:
        """Iterate over all QuamBase objects in this object, including nested objects.

        Args:
            skip_elems: A list of QuamBase objects to skip.
                This is used to prevent infinite loops when iterating over nested
                objects.

        Returns:
            A generator of QuamBase objects.
        """
        if skip_elems is None:
            skip_elems = []

        for attr_val in self.data:
            if any(attr_val is elem for elem in skip_elems):
                continue

            if isinstance(attr_val, QuamBase):
                yield from attr_val.iterate_components(skip_elems=skip_elems)

    def get_attrs(
        self, follow_references: bool = False, include_defaults: bool = True
    ) -> Dict[str, Any]:
        raise NotImplementedError("QuamList does not have attributes")

    def print_summary(self, indent: int = 0):
        """Print a summary of the QuamBase object.

        Args:
            indent: The number of spaces to indent the summary.
        """

        if self.parent is None:
            full_name = f"{self.__class__.__name__} (parent unknown):"
        else:
            try:
                attr_name = self.parent.get_attr_name(self)
                full_name = f"{attr_name}: {self.__class__.__name__}"
            except AttributeError:
                full_name = f"{self.__class__.__name__}:"

        if not self.data:
            print(" " * indent + f"{full_name} = []")
            return

        print(" " * indent + f"{full_name}:")
        if len(str(self.data)) + 2 * indent < 80:
            print(" " * (indent + 2) + f"{self.data}")
        else:
            for k, val in enumerate(self.data):
                if isinstance(val, QuamBase):
                    val.print_summary(indent=indent + 2)
                else:
                    print(" " * (indent + 2) + f"{k}: {val}")
