from typing import Union, Dict, Any
from pathlib import Path
import json

from quam_components.serialisation.base import AbstractSerialiser

from quam_components.core import QuamBase, QuamComponent


class JSONSerialiser(AbstractSerialiser):
    default_filename = "quam.json"
    default_foldername = "quam"
    component_mapping = {}

    def _save_dict_to_json(self, contents: Dict[str, Any], path: Path):
        with open(path, "w") as f:
            json.dump(contents, f, indent=4)

    def save(
        self,
        quam_obj: QuamBase,
        path: Union[Path, str] = None,
        component_mapping: Dict[str, str] = None,
        include_defaults: bool = False
    ):
        """


        No path, no component mapping -> save to default file
        No path, component mapping -> Create folder, save to default file, save components separately
        JSON Path, no component mapping -> Save to json file
        JSON Path, component mapping -> Save to json file, save components separately
        Folder Path, no component mapping -> Create folder, save to default file
        Folder Path, component mapping -> Create folder, save to default file, save components separately

        self.default_filename used when component_mapping is not None or no path provided
        self.default_foldername used when component_mapping is not None and path is not a folder
        """
        component_mapping = component_mapping or self.component_mapping

        contents = quam_obj.to_dict(include_defaults=include_defaults)

        if path is None:
            default_filename = self.default_filename
            if component_mapping:
                folder = self.default_foldername
            else:
                folder = Path(".")
        elif path.suffix == ".json":
            default_filename = path.name
            folder = path.parent
        elif not path.suffix:
            default_filename = self.default_filename
            folder = path
        else:
            raise ValueError(f"Path {path} is not a valid JSON path or folder.")

        folder.mkdir(exist_ok=True)

        component_mapping = component_mapping.copy()
        for component_filename, components in component_mapping.items():
            if isinstance(components, str):
                components = [components]

            subcomponents = {}
            for component in components:
                subcomponents[component] = contents.pop(component)

            self._save_dict_to_json(subcomponents, folder / component_filename)

        self._save_dict_to_json(contents, folder / default_filename)

    def load(
        self,
        path: Union[Path, str] = None,
    ):
        path = Path(path)
        contents = {}
        metadata = {
            "component_mapping": {},
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
                    metadata["component_mapping"][file.name] = list(
                        file_contents.keys()
                    )

        return contents, metadata
