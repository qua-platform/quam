from __future__ import annotations
from typing import Union, Dict, Any, TYPE_CHECKING, Sequence
from pathlib import Path
import json

from quam.serialisation.base import AbstractSerialiser

if TYPE_CHECKING:
    from quam.core import QuamRoot


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
    content_mapping = {}

    def _save_dict_to_json(self, contents: Dict[str, Any], path: Path):
        """Save a dictionary to a JSON file.

        Args:
            contents: The dictionary to save.
            path: The path to save to.
        """
        with open(path, "w") as f:
            json.dump(contents, f, indent=4)

    def _parse_path(
        self,
        path: Union[Path, str],
        content_mapping: Dict[Union[Path, str], Sequence[str]] = None,
    ) -> (Path, str):
        """Parse the path to determine the folder and filename to save to.

        See JSONSerialiser.save for details on allowed path types.

        Args:
            path: The path to parse.
            content_mapping: The content mapping to use.
        """
        if isinstance(path, str):
            path = Path(path)

        if path is None:
            default_filename = self.default_filename
            if not content_mapping:
                folder = Path(".")
            elif not all(isinstance(elem, Path) for elem in content_mapping):
                folder = Path(".")
            elif not all(elem.is_absolute() for elem in content_mapping):
                folder = Path(".")
            else:
                folder = self.default_foldername
        elif path.suffix == ".json":
            default_filename = path.name
            folder = path.parent
        elif not path.suffix:
            default_filename = self.default_filename
            folder = path
        else:
            raise ValueError(f"Path {path} is not a valid JSON path or folder.")

        return Path(folder), default_filename

    def save(
        self,
        quam_obj: QuamRoot,
        path: Union[Path, str] = None,
        content_mapping: Dict[Union[Path, str], Sequence[str]] = None,
        include_defaults: bool = False,
        ignore: Sequence[str] = None,
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
        content_mapping = content_mapping or self.content_mapping
        content_mapping = content_mapping.copy()

        contents = quam_obj.to_dict(include_defaults=include_defaults)

        # TODO This should ideally go to the QuamRoot.to_dict method
        for key in ignore or []:
            contents.pop(key, None)

        folder, default_filename = self._parse_path(path, content_mapping)

        folder.mkdir(exist_ok=True)

        content_mapping = content_mapping.copy()
        for component_file, components in content_mapping.items():
            if isinstance(components, str):
                components = [components]

            if ignore is not None:
                components = [elem for elem in components if elem not in ignore]
            if not components:
                continue

            subcomponents = {}
            for component in components:
                subcomponents[component] = contents.pop(component)

            if isinstance(component_file, Path) and component_file.is_absolute():
                component_filepath = component_file
            else:
                component_filepath = folder / component_file
            self._save_dict_to_json(subcomponents, component_filepath)

        self._save_dict_to_json(contents, folder / default_filename)

    def load(
        self,
        path: Union[Path, str] = None,
    ) -> Dict[str, Any]:
        """Load a dictionary representation of a QuamRoot object from a JSON file.

        Args:
            path: The path to load from. If a folder is provided, the contents from all
                JSON files in that folder are loaded and merged into a dictionary.
                If a JSON file is provided, the contents of that file are loaded.

        Returns:
            A dictionary representation of the QuamRoot object.
        """
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
        elif path.is_dir():
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
