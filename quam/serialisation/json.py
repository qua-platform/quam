from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple, Union

from .base import AbstractSerialiser

if TYPE_CHECKING:
    from quam.core import QuamRoot  # Assuming quam.core exists

# Type alias for content mapping flexibility
CONTENT_MAPPING_TYPE = Dict[str, Sequence[str]]
CONTENT_MAPPING_ALL_TYPES = Union[CONTENT_MAPPING_TYPE, List[CONTENT_MAPPING_TYPE]]


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
    Serialiser for QuAM objects to JSON files, allowing for splitting
    content across multiple files.

    Attributes:
        default_filename (str): Default filename if saving all content to one file.
        default_foldername (str): Default folder name if splitting content.
        content_mapping (CONTENT_MAPPING_ALL_TYPES): Defines how to split QuAM
            object content into different files. If empty, saves to a single file.
            Can be a single mapping dictionary or a list of mappings for multiple
            save configurations.
        include_defaults (bool): Whether to include default values in the
            serialised output.
        state_path (Optional[Path]): A specific path set during initialisation
            to be used as the default save/load location, overriding environment
            variables and configuration files.
    """

    default_filename: str = "state.json"
    default_foldername: str = "quam_state"
    content_mapping: CONTENT_MAPPING_ALL_TYPES = {}

    def __init__(
        self,
        content_mapping: Optional[CONTENT_MAPPING_ALL_TYPES] = None,
        include_defaults: bool = False,
        state_path: Optional[Union[str, Path]] = None,  # New argument
    ):
        """
        Initialises the JSONSerialiser.

        Args:
            content_mapping: A specific content mapping to use. If None, uses
                the class default. See class docstring for details.
            include_defaults: Whether to include fields set to their default
                values in the output. Defaults to False.
            state_path: An optional default path for saving/loading state. If provided,
                this path takes precedence over environment variables or configuration
                files when determining the default save/load location.
        """
        self.content_mapping = (
            content_mapping
            if content_mapping is not None
            else self.__class__.content_mapping
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
        with filepath.open("w", encoding="utf-8") as f:
            json.dump(contents, fp=f, indent=4, ensure_ascii=False)

    def _save_split_content(
        self,
        full_contents: Dict[str, Any],
        folder: Path,
        content_mapping: CONTENT_MAPPING_TYPE,
        ignore: Optional[Sequence[str]] = None,
    ):
        """
        Saves dictionary content split across multiple files in a folder
        based on the content_mapping.

        Args:
            full_contents: The complete dictionary of the QuAM object.
            folder: The target directory to save files into.
            content_mapping: Dictionary mapping filenames to lists of keys
                from full_contents.
            ignore: Optional list of top-level keys to ignore during saving.
        """
        remaining_contents = full_contents.copy()
        ignore_set = set(ignore or [])

        if not folder.exists():
            warnings.warn(
                f"QUAM state folder {folder} does not exist, creating it now.",
                UserWarning,
            )
            folder.mkdir(parents=True, exist_ok=True)

        # Remove ignored keys from the start
        for key in ignore_set:
            remaining_contents.pop(key, None)

        # Process each specified component file
        for filename, keys_to_save in content_mapping.items():

            # Ensure filename is relative and within the target folder
            component_file = Path(filename)
            if component_file.is_absolute():
                warnings.warn(
                    f"Absolute path '{filename}' in content_mapping is ignored. Using "
                    f"filename part only.",
                    UserWarning,
                )
                component_filepath = folder / component_file.name
            else:
                component_filepath = folder / component_file

            # Create subdirectories if specified in filename path
            if (
                component_filepath.parent != folder
                and not component_filepath.parent.exists()
            ):
                component_filepath.parent.mkdir(parents=True, exist_ok=True)

            partial_contents = {}
            keys_in_mapping = set(keys_to_save)

            # Collect specified keys, removing them from remaining_contents
            processed_keys = set()
            for key in list(remaining_contents.keys()):  # Iterate over copy of keys
                if key in keys_in_mapping:
                    partial_contents[key] = remaining_contents.pop(key)
                    processed_keys.add(key)

            # Warn if some requested keys were not found in the original object
            missing_keys = keys_in_mapping - processed_keys
            if missing_keys:
                warnings.warn(
                    f"Keys {list(missing_keys)} specified in content_mapping for "
                    f"{filename} not found in QuAM object or already ignored.",
                    UserWarning,
                )

            if not partial_contents:
                # Warn instead of skipping file creation if keys were specified but missing/ignored
                if (
                    keys_in_mapping
                ):  # Only warn if keys were actually requested for this file
                    warnings.warn(
                        f"No content found for keys {list(keys_in_mapping)} specified for "
                        f"{filename}. File will not be created.",
                        UserWarning,
                    )
                continue  # Skip creating empty files

            self._save_dict_to_json(partial_contents, component_filepath)

        # Save any remaining contents to the default file
        if remaining_contents:
            default_filepath = folder / self.default_filename
            self._save_dict_to_json(remaining_contents, default_filepath)
        elif not content_mapping and not ignore_set and not full_contents:
            # Only create empty default file if there was truly no content to begin with
            # and no splitting/ignoring happened. Avoids creating empty default file
            # when splitting consumes all content.
            default_filepath = folder / self.default_filename
            self._save_dict_to_json({}, default_filepath)
            warnings.warn(
                f"Saved empty default file to {default_filepath}", UserWarning
            )

    def save(
        self,
        quam_obj: QuamRoot,
        path: Optional[Union[Path, str]] = None,
        content_mapping: Optional[CONTENT_MAPPING_ALL_TYPES] = None,
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
            include_defaults: Overrides the instance's include_defaults for this save.
            ignore: A sequence of top-level keys in the QuAM object to exclude
                    from the saved output.
        """
        # Use provided args or fall back to instance defaults
        current_content_mapping = (
            content_mapping if content_mapping is not None else self.content_mapping
        )
        current_include_defaults = (
            include_defaults if include_defaults is not None else self.include_defaults
        )

        # Handle list of content mappings by recursive calls
        if isinstance(current_content_mapping, list):
            for mapping_item in current_content_mapping:
                # Recursively call save for each mapping in the list
                self.save(
                    quam_obj=quam_obj,
                    path=path,  # Pass original path arg through
                    content_mapping=mapping_item,  # Use the specific mapping item
                    include_defaults=current_include_defaults,
                    ignore=ignore,
                )
            return  # Stop processing after handling the list

        if path is None:
            path = self._get_state_path()
        path = Path(path)

        # Get the dictionary representation of the object
        contents_dict = quam_obj.to_dict(include_defaults=current_include_defaults)

        if ignore:
            contents_dict = {k: v for k, v in contents_dict.items() if k not in ignore}

        if path.suffix == ".json":
            # Target is a json file, save content to it
            self._save_dict_to_json(contents_dict, path)
        elif not path.suffix:
            self._save_split_content(
                full_contents=contents_dict,
                folder=path,
                content_mapping=current_content_mapping,
                ignore=ignore,
            )
        else:
            raise ValueError(f"Cannot save QUAM: Unsupported {path.suffix=}")

    def _get_state_path(self) -> Path:  # Renamed from _get_default_state_path
        """
        Determines the default path for saving/loading state.

        Resolution order:
        1. `self.state_path` (if set during `__init__`).
        2. `QUAM_STATE_PATH` environment variable.
        3. `state_path` from QuAM configuration (via `get_quam_config`).

        Returns:
            The default Path object, resolved to an absolute path.

        Raises:
            ValueError: If no path can be found via instance, environment, or config.
        """
        # 1. Check instance path first
        if self.state_path is not None:
            # Ensure it's resolved (already done in init, but safe to repeat)
            return self.state_path.resolve()

        # 2. Check environment variable
        if "QUAM_STATE_PATH" in os.environ:
            return Path(os.environ["QUAM_STATE_PATH"]).resolve()

        # 3. Check configuration file
        try:
            # Attempt to import and use quam.config dynamically
            from quam.config import get_quam_config

            cfg = get_quam_config()
            if cfg and cfg.state_path is not None:
                return Path(cfg.state_path).resolve()
        except ImportError:
            warnings.warn(
                "Optional 'quam.config' not found. Cannot check config for state path.",
                ImportWarning,
            )
        except AttributeError:
            warnings.warn(
                "'get_quam_config' or 'state_path' not available in 'quam.config'. Cannot check config.",
                UserWarning,
            )

        # 4. No path found
        raise ValueError(
            "No state path found. Set state_path during init, set QUAM_STATE_PATH "
            "environment variable, or configure state_path in quam config."
        )

    def _load_from_file(self, filepath: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Loads dictionary content from a single JSON file.

        Args:
            filepath: The exact path to the JSON file.

        Returns:
            A tuple containing:
            1. The loaded dictionary content.
            2. Metadata dictionary including inferred 'content_mapping',
               'default_filename', and 'default_foldername'.

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

            # Basic metadata for single file load
            metadata = {
                "content_mapping": {},  # No mapping inferred from single file
                "default_filename": filepath.name,
                "default_foldername": None,  # Not loaded from a folder
            }
            return contents, metadata
        except json.JSONDecodeError as e:
            # Raise with more context
            raise json.JSONDecodeError(
                f"Error decoding JSON from {filepath}: {e.msg}", e.doc, e.pos
            ) from e
        except IOError as e:
            raise IOError(f"Error reading file {filepath}: {e}") from e

    def _load_from_directory(
        self, dirpath: Path
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Loads and merges content from all .json files in a directory.

        Args:
            dirpath: The path to the directory to load from.

        Returns:
            A tuple containing:
            1. The merged dictionary content from all JSON files.
            2. Metadata dictionary including inferred 'content_mapping',
               'default_filename', and 'default_foldername'.
        """
        contents: Dict[str, Any] = {}
        metadata: Dict[str, Any] = {
            "content_mapping": {},
            "default_filename": None,
            "default_foldername": str(dirpath),  # Store the dir path loaded from
        }

        found_files = list(dirpath.glob("*.json"))

        if not found_files:
            warnings.warn(f"No JSON files found in directory {dirpath}", UserWarning)
            return contents, metadata  # Return empty content and basic metadata

        for file in found_files:
            try:
                # Use the _load_from_file helper for individual file loading
                file_contents, _ = self._load_from_file(file)

                # Check for key conflicts before updating
                conflicts = contents.keys() & file_contents.keys()
                if conflicts:
                    warnings.warn(
                        f"Keys {list(conflicts)} from {file.name} overwrite "
                        f"existing keys while loading from directory {dirpath}.",
                        UserWarning,
                    )
                contents.update(file_contents)

                # Update metadata based on filenames
                if file.name == self.default_filename:
                    metadata["default_filename"] = file.name
                else:
                    # Store which keys came from which file (approximates content_mapping)
                    metadata["content_mapping"][file.name] = list(file_contents.keys())

            except (json.JSONDecodeError, IOError, TypeError) as e:
                # Catch errors from _load_from_file and warn
                warnings.warn(f"Skipping file {file}: {e}", UserWarning)

        return contents, metadata

    def load(
        self,
        path: Optional[Union[Path, str]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Loads a QuamRoot object's dictionary representation from JSON file(s).

        Determines the load path using the provided `path` argument or falls back
        to default logic (instance `state_path`, env var, config).

        If the resolved path points to a single JSON file, it loads that file.
        If the resolved path points to a directory, it loads and merges content
        from all `.json` files within that directory using `_load_from_directory`.

        Args:
            path: The path to load from (file or directory). If None, uses the
                  default state path logic via `_get_state_path()`.

        Returns:
            A tuple containing:
            1. Dictionary representation of the loaded QuAM object.
            2. Metadata dictionary containing inferred loading details like
               'content_mapping', 'default_filename', 'default_foldername'.

        Raises:
            FileNotFoundError: If the resolved path does not exist.
            ValueError: If the resolved path is neither a file nor a directory
                        (should not typically occur after existence check).
        """
        load_path: Path
        if path is None:
            load_path = self._get_state_path()  # Use updated logic
        else:
            load_path = Path(path).resolve()

        if not load_path.exists():
            raise FileNotFoundError(f"Path {load_path} not found, cannot load JSON.")

        contents: Dict[str, Any]
        metadata: Dict[str, Any]

        if load_path.is_file():
            # Load from a single file
            contents, metadata = self._load_from_file(load_path)
        elif load_path.is_dir():
            # Load from a directory, merging contents
            contents, metadata = self._load_from_directory(load_path)
        else:
            # Path exists but is not a file or directory (e.g., broken symlink?)
            raise ValueError(f"Path {load_path} is neither a valid file nor directory.")

        return contents, metadata
