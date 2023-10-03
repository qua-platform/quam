from __future__ import annotations
from typing import Union, Dict, Any, TYPE_CHECKING, Sequence
from pathlib import Path
import json

from quam.serialisation.base import AbstractSerialiser

if TYPE_CHECKING:
    from quam.core import QuamRoot


class JSONSerialiser(AbstractSerialiser):
    default_filename = "state.json"
    default_foldername = "quam"
    content_mapping = {}

    def _save_dict_to_json(self, contents: Dict[str, Any], path: Path):
        with open(path, "w") as f:
            json.dump(contents, f, indent=4)

    def _parse_path(
        self,
        path: Union[Path, str],
        content_mapping: Dict[Union[Path, str], Sequence[str]] = None,
    ) -> (Path, str):
        """Parse the path to determine the folder and filename to save to.

        See JSONSerialiser.save for details on allowed path types.
        """
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
            contents.pop(key)

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
    ):
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
                contents = json.load(f)
        elif path.is_dir():
            metadata["default_foldername"] = str(path)
            for file in path.iterdir():
                if not file.suffix == ".json":
                    continue

                with open(file, "r") as f:
                    file_contents = json.load(f)
                contents.update(file_contents)

                if file.name == self.default_filename:
                    metadata["default_filename"] = file.name
                else:
                    metadata["content_mapping"][file.name] = list(file_contents.keys())

        return contents, metadata
