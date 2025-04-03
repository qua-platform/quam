from __future__ import annotations
from typing import Union, Dict, Any, TYPE_CHECKING, Sequence, Optional, List, Tuple
from pathlib import Path
import os
import json
import warnings

from quam.serialisation.base import AbstractSerialiser

if TYPE_CHECKING:
    from quam.core import QuamRoot


CONTENT_MAPPING_ALL_TYPES = Union[
    Dict[str, Sequence[str]], List[Dict[str, Sequence[str]]]
]


class JSONSerialiser(AbstractSerialiser):
    """Serialiser for QuAM objects to JSON files.

    Args:
        default_filename: The default filename to save to when no filename is provided.
        default_foldername: The default foldername to save to when no folder is
            provided. Only used when saving components to separate files, i.e. when
            `component_mapping` is provided.
        content_mapping: A dictionary mapping filenames to the keys of the contents
            to be saved to that file. If not provided, all contents are saved to the
            default file, otherwise a folder is created and the default file is saved
            to that folder, and the contents are saved to the files specified in the
            mapping.
    """

    default_filename = "state.json"
    default_foldername = "quam"
    content_mapping: CONTENT_MAPPING_ALL_TYPES = {}

    def __init__(
        self,
        content_mapping: Optional[CONTENT_MAPPING_ALL_TYPES] = None,
        include_defaults: bool = False,
    ):
        if content_mapping is None:
            self.content_mapping = self.__class__.content_mapping
        else:
            self.content_mapping = content_mapping

        self.include_defaults = include_defaults

    def _save_dict_to_json(
        self, contents: Dict[str, Any], path: Path, create_parents: bool = True
    ):
        """Save a dictionary to a JSON file.

        Args:
            contents: The dictionary to save.
            path: The path to save to.
            create_parents: Whether to create the parent directories if they don't exist
        """
        if not path.parent.exists() and create_parents:
            warnings.warn(
                f"Creating non-existent QUAM state parent folder {path.parent}",
                UserWarning,
            )
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(contents, fp=f, indent=4)

    def save(
        self,
        quam_obj: QuamRoot,
        path: Optional[Union[Path, str]] = None,
        content_mapping: Optional[
            Union[Dict[str, Sequence[str]], List[Dict[str, Sequence[str]]]]
        ] = None,
        include_defaults: Optional[bool] = None,
        ignore: Optional[Sequence[str]] = None,
    ):
        """Save a QuamRoot object to a JSON file.

        The save location depends on the path provided and the content_mapping.
            No path, no component mapping -> save to default file
            No path, component mapping -> Create folder, save to default file,
                save components separately
            JSON Path, no component mapping -> Save to json file
            JSON Path, component mapping -> Save to json file, save components
                separately
            Folder Path, no component mapping -> Create folder, save to default file
            Folder Path, component mapping -> Create folder, save to default file,
                save components separately

            self.default_filename when content_mapping != None or no path provided
            self.default_foldername when content_mapping != None and path is not a
                folder
        """
        if content_mapping is None:
            content_mapping = self.content_mapping
        content_mapping = content_mapping.copy()

        if isinstance(content_mapping, list):
            for content_mapping_item in content_mapping:
                self.save(
                    quam_obj=quam_obj,
                    path=path,
                    content_mapping=content_mapping_item,
                    include_defaults=include_defaults,
                    ignore=ignore,
                )
            return

        if include_defaults is None:
            include_defaults = self.include_defaults

        contents = quam_obj.to_dict(include_defaults=include_defaults)

        # TODO This should ideally go to the QuamRoot.to_dict method
        for key in ignore or []:
            contents.pop(key, None)

        if path is None:
            path = self._get_default_state_path()
        path = Path(path)

        if path.suffix == ".json":
            self._save_dict_to_json(contents, path)
        elif not path.suffix:
            self._save_dict_to_folder(
                contents,
                path,
                content_mapping=content_mapping,
                ignore=ignore,
            )
        else:
            raise ValueError(
                f"Cannot save QUAM, state path {path} is not a JSON path or folder."
            )

    def _save_dict_to_folder(
        self,
        contents: Dict[str, Any],
        folder: Path,
        content_mapping: Dict[str, Sequence[str]],
        default_filename: Optional[str] = None,
        ignore: Optional[Sequence[str]] = None,
    ):
        if not folder.exists():
            warnings.warn(
                f"Creating non-existent QUAM state folder {folder}",
                UserWarning,
            )
            folder.mkdir(parents=True, exist_ok=True)

        if default_filename is None:
            default_filename = self.default_filename

        content_mapping = content_mapping.copy()

        for component_file, components in content_mapping.items():
            component_file = Path(component_file)

            if isinstance(components, str):
                components = [components]
            if ignore is not None:
                components = [elem for elem in components if elem not in ignore]

            partial_contents = {}
            for component in components:
                if component not in contents:
                    warnings.warn(
                        f"Component {component} not found in QUAM state, skipping.",
                        UserWarning,
                    )
                    continue
                partial_contents[component] = contents.pop(component)

            if not partial_contents:
                # There is nothing to save for this component
                continue

            if component_file.is_absolute():
                component_filepath = component_file
            else:
                component_filepath = folder / component_file
            self._save_dict_to_json(partial_contents, component_filepath)

        if contents:
            self._save_dict_to_json(contents, folder / default_filename)

    def _get_default_state_path(self) -> Path:
        if "QUAM_STATE_PATH" in os.environ:
            return Path(os.environ["QUAM_STATE_PATH"])

        from quam.config import get_quam_config

        cfg = get_quam_config()

        if cfg.state_path is not None:
            return cfg.state_path

        raise ValueError("No default QUAM state path found")

    def load(
        self,
        path: Optional[Union[Path, str]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Load a dictionary representation of a QuamRoot object from a JSON file.

        Args:
            path: The path to load from. If a folder is provided, the contents from all
                JSON files in that folder are loaded and merged into a dictionary.
                If a JSON file is provided, the contents of that file are loaded.

        Returns:
            A dictionary representation of the QuamRoot object.
        """

        if path is None:
            path = self._get_default_state_path()
        else:
            path = Path(path)

        contents = {}
        metadata = {
            "content_mapping": {},
            "default_filename": None,
            "default_foldername": None,
        }

        if not path.exists():
            raise FileNotFoundError(f"Path {path} not found, cannot load JSON.")

        if path.is_file():
            if not path.suffix == ".json":
                raise TypeError(f"File {path} is not a JSON file.")

            metadata["default_filename"] = path.name
            with open(path, "r") as f:
                contents = json.load(f, object_hook=convert_int_keys)

            return contents, metadata

        if path.is_dir():
            metadata["default_foldername"] = str(path)
            for file in path.iterdir():
                if not file.suffix == ".json":
                    continue

                with open(file, "r") as f:
                    file_contents = json.load(f, object_hook=convert_int_keys)
                contents.update(file_contents)

                if file.name == self.default_filename:
                    metadata["default_filename"] = file.name
                else:
                    metadata["content_mapping"][file.name] = list(file_contents.keys())

        return contents, metadata


def convert_int_keys(obj):
    """Convert dictionary keys to integers if possible."""
    if not isinstance(obj, dict):
        return obj

    new_obj = {}
    for key, value in obj.items():
        if key.isdigit():
            key = int(key)
        new_obj[key] = value

    return new_obj
