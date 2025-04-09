from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Tuple, Union, List

from quam.config import get_quam_config
from .base import AbstractSerialiser

if TYPE_CHECKING:
    from quam.core import QuamRoot  # Assuming quam.core exists


def convert_int_keys(obj: Any) -> Any:
    """
    JSON object hook to convert dictionary keys that are strings
    representing integers back into integers during loading.

    Args:
        obj: The object being processed by the JSON decoder.

    Returns:
        The processed object, with relevant keys converted to integers.
    """
    if not isinstance(obj, dict):
        return obj

    new_obj = {}
    for key, value in obj.items():
        try:
            # Attempt to convert key to int if it represents a digit
            int_key = int(key)
            new_obj[int_key] = value
        except ValueError:
            # Keep the original string key if conversion fails
            new_obj[key] = value
    return new_obj


class JSONSerialiser(AbstractSerialiser):
    """
    Serialiser for QUAM objects to JSON files, allowing for splitting
    content across multiple files.

    Attributes:
        default_filename (str): Default filename if saving all content to one file.
        default_foldername (str): Default folder name if splitting content.
        content_mapping (Dict[str, str]): Defines how to split QUAM
            object content into different files. Keys are component names (top-level
            keys in the QUAM object's dictionary representation), and values are the
            relative filenames they should be saved to. If empty, saves to a single file
        include_defaults (bool): Whether to include default values in the
            serialised output.
        state_path (Optional[Path]): A specific path set during initialisation
            to be used as the default save/load location, overriding environment
            variables and configuration files.
    """

    default_filename: str = "state.json"
    default_foldername: str = "quam_state"
    content_mapping: Dict[str, str] = {}  # Expected final format: component -> filename

    @staticmethod
    def _validate_and_convert_content_mapping(
        mapping: Optional[Dict],
    ) -> Dict[str, str]:
        """
        Validates the content_mapping format and converts the old format
        (filename -> components) to the new format (component -> filename)
        if necessary, issuing a warning.

        Args:
            mapping: The content mapping dictionary to validate/convert.

        Returns:
            The validated content mapping in the new format (component -> filename).

        Raises:
            TypeError: If the mapping format is invalid (e.g., mixed value types).
        """
        if mapping is None:
            return {}

        if not isinstance(mapping, dict):
            raise TypeError(
                f"content_mapping must be a dictionary, got {type(mapping)}"
            )

        if not mapping:
            return {}

        # Check the type of the first value to infer format
        first_value = next(iter(mapping.values()))
        is_old_format = isinstance(
            first_value, (list, tuple, set, Sequence)
        ) and not isinstance(first_value, str)
        is_new_format = isinstance(first_value, str)

        if is_old_format:
            # Handle Old Format
            new_mapping: Dict[str, str] = {}
            conflicts: Dict[str, List[str]] = {}

            for filename, components in mapping.items():
                if not isinstance(filename, str):
                    raise TypeError(
                        "Invalid key in old format content_mapping: Expected string "
                        f"filename, got {type(filename)} ({filename})"
                    )
                if not isinstance(
                    components, (list, tuple, set, Sequence)
                ) or isinstance(components, str):
                    # Check for mixed formats within the old format assumption
                    raise TypeError(
                        "Mixed value types detected in content_mapping. Assumed old"
                        " format (filename -> components) based on first value, but"
                        f" found non-sequence value '{components}' for key"
                        f" '{filename}'."
                    )

                for component in components:
                    if not isinstance(component, str):
                        raise TypeError(
                            "Invalid component name in old format content_mapping:"
                            f" Expected string, got {type(component)} ({component}) in"
                            f" list for file '{filename}'"
                        )
                    if component in new_mapping:
                        conflicts.setdefault(
                            component, [new_mapping[component]]
                        ).append(filename)
                    new_mapping[component] = filename

            # Issue warnings for conflicts
            if conflicts:
                conflict_details = "; ".join(
                    [
                        f"'{comp}': [{', '.join(map(repr, files))}]"
                        for comp, files in conflicts.items()
                    ]
                )
                warnings.warn(
                    "Component conflicts detected in old format content_mapping. "
                    f"Components assigned to multiple files: {conflict_details}. "
                    "Using the last assignment found.",
                    UserWarning,
                )

            # Issue the main conversion warning
            old_repr = repr(mapping)
            new_repr = repr(new_mapping)
            warnings.warn(
                "Detected deprecated content_mapping format (filename -> components"
                " list).\nAutomatically converted to the new format (component ->"
                f" filename).\nOld mapping: {old_repr}\nConverted to:"
                f" {new_repr}\nPlease update your code to use the new format for future"
                " compatibility.",
                DeprecationWarning,
                stacklevel=3,  # Point warning towards the caller of __init__ or save
            )
            return new_mapping

        elif is_new_format:
            # Handle New Format
            # Validate that all values are strings
            for key, value in mapping.items():
                if not isinstance(key, str):
                    raise TypeError(
                        "Invalid key in new format content_mapping: Expected string"
                        f" component name, got {type(key)} ({key})"
                    )
                if not isinstance(value, str):
                    # Check for mixed formats within the new format assumption
                    raise TypeError(
                        "Mixed value types detected in content_mapping. Assumed new"
                        " format (component -> filename) based on first value, but"
                        f" found non-string value '{value}' for key '{key}'."
                    )
            return mapping  # Already in the correct format
        else:
            # Handle Invalid Format
            raise TypeError(
                "Invalid format for content_mapping. Values must be either all strings"
                " (component -> filename) or all sequences (filename -> components),"
                f" but found type {type(first_value)} for the first value."
            )

    def __init__(
        self,
        content_mapping: Optional[Dict] = None,  # Accept Dict initially for validation
        include_defaults: bool = False,
        state_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialises the JSONSerialiser.

        Args:
            content_mapping: A specific content mapping to use. Can be in the old
                (filename->components) or new (component->filename) format. If old
                format is detected, a warning is issued and it's converted.
                If None, uses the class default.
            include_defaults: Whether to include fields set to their default
                values in the output. Defaults to False.
            state_path: An optional default path for saving/loading state. If provided,
                this path takes precedence over environment variables or configuration
                files when determining the default save/load location.
        """
        initial_mapping = (
            content_mapping
            if content_mapping is not None
            else self.__class__.content_mapping
        )
        # Validate and potentially convert the mapping
        self.content_mapping = self._validate_and_convert_content_mapping(
            initial_mapping
        )

        self.include_defaults = include_defaults
        # Store the state_path, resolving it if provided
        self.state_path: Optional[Path] = (
            Path(state_path).resolve() if state_path else None
        )

    def _save_dict_to_json(self, contents: Dict[str, Any], filepath: Path):
        """
        Saves a dictionary to a specified JSON file.

        Args:
            contents: The dictionary to save.
            filepath: The exact path to the JSON file.
        """
        # Ensure parent directory exists just before writing
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w", encoding="utf-8") as f:
            json.dump(contents, fp=f, indent=4, ensure_ascii=False)

    def _save_split_content(
        self,
        full_contents: Dict[str, Any],
        folder: Path,
        content_mapping: Dict[str, str],  # Expects new format here
    ):
        """
        Saves dictionary content split across multiple files in a folder
        based on the content_mapping (component -> filename format).

        Args:
            full_contents: The complete dictionary of the QUAM object.
            folder: The target directory to save files into.
            content_mapping: Dictionary mapping component names (keys) to
                relative filenames (values). Old format (filename -> components)
                is not supported in this method.
        """
        remaining_contents = full_contents.copy()
        files_to_save: Dict[Path, Dict[str, Any]] = (
            {}
        )  # Stores filepath -> content dict

        # Iterate through components and assign them to files based on mapping
        mapped_keys = set()
        for component_key, filename in content_mapping.items():
            if component_key in remaining_contents:
                # Resolve the filepath
                component_file = Path(filename)
                if component_file.is_absolute():
                    warnings.warn(
                        f"Absolute path '{filename}' in content_mapping is ignored. "
                        f"Using filename part only relative to '{folder}'.",
                        UserWarning,
                    )
                    component_filepath = folder / component_file.name
                else:
                    component_filepath = folder / component_file

                # Add component to the dictionary for this file
                if component_filepath not in files_to_save:
                    files_to_save[component_filepath] = {}
                files_to_save[component_filepath][component_key] = (
                    remaining_contents.pop(component_key)
                )
                mapped_keys.add(component_key)
            else:
                warnings.warn(
                    f"Key '{component_key}' specified in content_mapping was not found "
                    "in the QUAM object's data",
                    UserWarning,
                )

        # Save the collected components to their respective files
        for filepath, file_contents in files_to_save.items():
            self._save_dict_to_json(file_contents, filepath)

        # Save any remaining contents to the default file
        if remaining_contents:
            default_filepath = folder / self.default_filename
            self._save_dict_to_json(remaining_contents, default_filepath)

    def save(
        self,
        quam_obj: QuamRoot,
        path: Optional[Union[Path, str]] = None,
        content_mapping: Optional[Dict] = None,  # Accept Dict initially
        include_defaults: Optional[bool] = None,
        ignore: Optional[Sequence[str]] = None,
    ):
        """
        Saves a QuamRoot object to JSON file(s).

        Determines the save location and format (single file vs. split) based
        on the provided path and content_mapping arguments, falling back to
        instance/class defaults if arguments are None.

        Args:
            quam_obj: The QuamRoot object to serialise.
            path: The target file or folder path. If None, uses default path logic
                  (checking instance `state_path`, env var, config).
            content_mapping: Overrides the instance's content_mapping for this save.
                Can be in old or new format. If old format is provided, a warning is
                issued and it's converted internally.
            include_defaults: Overrides the instance's include_defaults for this save.
            ignore: A sequence of top-level keys in the QUAM object to exclude
                    from the saved output.
        """
        # Validate and convert the provided content_mapping, or use the instance's
        # (already validated) one
        if content_mapping is not None:
            current_content_mapping = self._validate_and_convert_content_mapping(
                content_mapping
            )
        else:
            current_content_mapping = self.content_mapping  # Already validated in init

        current_include_defaults = (
            include_defaults if include_defaults is not None else self.include_defaults
        )

        if path is None:
            path = self._get_state_path()
        path = Path(path)

        # Get the dictionary representation of the object
        contents_dict = quam_obj.to_dict(include_defaults=current_include_defaults)

        # Apply ignore filter directly to the source dictionary before saving
        # This modification is temporary for the save operation.
        effective_contents = contents_dict.copy()
        if ignore:
            current_content_mapping = current_content_mapping.copy()
            for key in ignore:
                effective_contents.pop(key, None)  # Modify the copy
                current_content_mapping.pop(key, None)

        if path.suffix == ".json":
            # Target is a json file, save content to it
            self._save_dict_to_json(effective_contents, path)
        elif not path.suffix:
            # Target is a directory, use split logic
            self._save_split_content(
                full_contents=effective_contents,
                folder=path,
                content_mapping=current_content_mapping,  # Pass validated mapping
            )
        else:
            raise ValueError(
                f"Cannot save QUAM: Unsupported path suffix '{path.suffix}'"
            )

    def _get_state_path(self) -> Path:
        """
        Determines the default path for saving/loading state.

        Resolution order:
        1. `self.state_path` (if set during `__init__`).
        2. `QUAM_STATE_PATH` environment variable.
        3. `state_path` from QUAM configuration (via `get_quam_config`).
        4. Fallback to `default_foldername` or `default_filename` in the current
           directory.

        Returns:
            The default Path object, resolved to an absolute path.
        """
        # 1. Check instance path first
        if self.state_path is not None:
            return self.state_path.resolve()

        # 2. Check environment variable
        env_path = os.environ.get("QUAM_STATE_PATH")
        if env_path:
            return Path(env_path).resolve()

        # 3. Check configuration file
        try:
            cfg = get_quam_config()
            if cfg and cfg.state_path is not None:
                return Path(cfg.state_path).resolve()

        except (AttributeError, FileNotFoundError):  # Catch potential errors
            warnings.warn(
                "Could not determine state path from QUAM configuration. "
                "Falling back to environment or default.",
                UserWarning,
            )

        # 4. No path found - Fallback to saving in current directory
        # Decide on using the folder or single file default based on content_mapping
        # Use the mapping already validated/converted in __init__
        if self.content_mapping:
            default_path = Path(self.default_foldername)
            warnings.warn(
                "No state path found via init, environment, or config. Defaulting "
                f"to folder '{default_path}' in the current directory because "
                "content_mapping is defined.",
                UserWarning,
            )
        else:
            default_path = Path(self.default_filename)
            warnings.warn(
                "No state path found via init, environment, or config. Defaulting "
                f"to file '{default_path}' in the current directory.",
                UserWarning,
            )
        return default_path.resolve()

    def _load_from_file(self, filepath: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Loads dictionary content from a single JSON file.

        Args:
            filepath: The exact path to the JSON file.

        Returns:
            A tuple containing:
            1. The loaded dictionary content.
            2. Metadata dictionary including inferred 'content_mapping
               (component -> filename), 'default_filename', and
               'default_foldername'.

        Raises:
            TypeError: If the filepath does not have a .json suffix.
            json.JSONDecodeError: If the file content is invalid JSON.
            IOError: If the file cannot be read.
        """
        if filepath.suffix.lower() != ".json":
            raise TypeError(f"File {filepath} is not a JSON file.")

        try:
            with filepath.open("r", encoding="utf-8") as f:
                contents = json.load(f, object_hook=convert_int_keys)
            if not isinstance(contents, dict):
                raise TypeError(
                    f"File {filepath} does not contain a valid JSON dictionary.",
                )

            metadata = {
                "content_mapping": {},
                "default_filename": filepath.name,
                "default_foldername": None,
            }
            return contents, metadata
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Error decoding JSON from {filepath}: {e.msg}", e.doc, e.pos
            ) from e
        except IOError as e:
            raise IOError(f"Error reading file {filepath}: {e}") from e
        except Exception as e:  # Catch unexpected errors during loading
            raise RuntimeError(
                f"An unexpected error occurred while loading {filepath}: {e}"
            ) from e

    def _load_from_directory(
        self, dirpath: Path
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Loads and merges content from all .json files in a directory and its
        subdirectories. Infers the content mapping (component -> filename).

        Args:
            dirpath: The path to the directory to load from.

        Returns:
            A tuple containing:
            1. The merged dictionary content.
            2. Metadata dictionary including inferred 'content_mapping',
               'default_filename', and 'default_foldername'.
        """
        contents: Dict[str, Any] = {}
        inferred_mapping: Dict[str, str] = {}  # component -> relative_filename
        metadata: Dict[str, Any] = {
            "content_mapping": inferred_mapping,
            "default_filename": None,
            "default_foldername": str(dirpath.resolve()),
        }

        found_files = list(dirpath.rglob("*.json"))

        if not found_files:
            warnings.warn(f"No JSON files found in directory {dirpath}", UserWarning)
            return contents, metadata

        processed_files_count = 0
        for file in found_files:
            try:
                file_contents, _ = self._load_from_file(
                    file
                )  # Metadata from single file load is not needed here
                if not file_contents:  # Skip empty files
                    warnings.warn(
                        f"Skipping empty or invalid JSON file: {file}", UserWarning
                    )
                    continue

                relative_filepath = file.relative_to(dirpath).as_posix()
                processed_files_count += 1

                # Check for key conflicts before updating contents
                conflicts = contents.keys() & file_contents.keys()
                if conflicts:
                    conflict_details = {
                        key: inferred_mapping[key]
                        for key in conflicts
                        if key in inferred_mapping
                    }
                    warnings.warn(
                        f"Key conflicts detected: Components {list(conflicts)} found in"
                        f" '{relative_filepath}' overwrite existing definitions from"
                        f" files {conflict_details}. Using definition from"
                        f" '{relative_filepath}'.",
                        UserWarning,
                    )
                contents.update(file_contents)

                # Update inferred mapping: component -> relative_filepath
                for key in file_contents.keys():
                    # Overwrite mapping on conflict
                    inferred_mapping[key] = relative_filepath

                # Check if this file is the default file at the root level
                if file.name == self.default_filename and file.parent == dirpath:
                    metadata["default_filename"] = file.name

            except (
                json.JSONDecodeError,
                IOError,
                TypeError,
                RuntimeError,
            ) as e:
                warnings.warn(f"Skipping file {file} due to error: {e}", UserWarning)

        if processed_files_count == 0 and found_files:
            warnings.warn(
                f"Found {len(found_files)} JSON files in {dirpath}, but none contained"
                " valid data.",
                UserWarning,
            )

        # Filter out inferred_mapping keys that point to the default file
        inferred_mapping = {
            key: value
            for key, value in inferred_mapping.items()
            if value != self.default_filename
        }

        metadata["content_mapping"] = inferred_mapping
        return contents, metadata

    def load(
        self,
        path: Optional[Union[Path, str]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Loads a QuamRoot object's dictionary representation from JSON file(s).

        Determines the load path using the provided `path` argument or falls back
        to default logic (instance `state_path`, env var, config). Loads from a
        single file or merges from a directory (recursively).

        Args:
            path: The path to load from (file or directory). If None, uses the
                  default state path logic via `_get_state_path()`.

        Returns:
            A tuple containing:
            1. Dictionary representation of the loaded QUAM object.
            2. Metadata dictionary including inferred 'content_mapping' (component ->
               filename), 'default_filename', 'default_foldername'.

        Raises:
            FileNotFoundError: If the resolved path does not exist.
            ValueError: If the resolved path is neither a file nor a directory.
        """
        load_path: Path
        if path is None:
            load_path = self._get_state_path()
        else:
            load_path = Path(path).resolve()

        if not load_path.exists():
            raise FileNotFoundError(f"Path {load_path} not found, cannot load JSON.")

        contents: Dict[str, Any]
        metadata: Dict[str, Any]

        if load_path.is_file():
            contents, metadata = self._load_from_file(load_path)
        elif load_path.is_dir():
            contents, metadata = self._load_from_directory(load_path)
        else:
            raise ValueError(f"Path {load_path} is neither a valid file nor directory.")

        # Update the instance's content_mapping *only if* it wasn't explicitly set
        # during initialization or via the save method argument override.
        is_default_mapping = self.content_mapping == self.__class__.content_mapping
        if is_default_mapping and "content_mapping" in metadata:
            self.content_mapping = metadata["content_mapping"]

        return contents, metadata
