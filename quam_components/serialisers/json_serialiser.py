from typing import Union, Dict
from pathlib import Path
import json

from quam_components.core import QuamBase, QuamComponent
from quam_components.serialisers.base import AbstractSerialiser


class JSONSerialiser(AbstractSerialiser):
    default_filename = "quam.json"
    default_foldername = "quam"
    component_mapping = {}

    def save(
        self,
        quam_obj: Union[QuamBase, QuamComponent],
        path: Union[Path, str] = None,
        component_mapping: Dict[str, str] = None,
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

        contents = quam_obj.to_dict()

        if path is None:
            default_filename = self.default_filename
            if component_mapping:
                folder = self.default_foldername
            else:
                folder = Path('.')
        elif path.suffix == ".json":
            default_filename = path.name
            folder = path.parent
        elif not path.suffix:
            default_filename = self.default_filename
            folder = path
        else:
            raise ValueError(f"Path {path} is not a valid JSON path or folder.")

        folder.mkdir(exist_ok=True)

        if component_mapping:
            component_mapping = component_mapping.copy()
            for component_filename, components in component_mapping.items():
                subcomponents = {}
                for component in components:
                    subcomponents[component] = contents.pop(component)

                with open(folder / component_filename, "w") as f:
                    json.dump(subcomponents, f)

        with open(folder / default_filename, "w") as f:
            json.dump(contents, f)

    def load(
        self,
        path: Union[Path, str] = None,
    ):
        path = Path(path)
        results = {
            "contents": {},
            "component_mapping": {},
            "default_filename": None,
            "default_foldername": None,
        }

        if not path.exists():
            raise FileNotFoundError(f"Path {path} not found, cannot load JSON.")

        if path.is_file():
            if not path.suffix == ".json":
                raise TypeError(f"File {path} is not a JSON file.")

            results["default_filename"] = path.name
            with open(path, "r") as f:
                results["contents"] = json.load(f)
        elif path.is_dir():
            results["default_foldername"] = path.name
            for file in path.iterdir():
                if not file.suffix == ".json":
                    continue

                with open(file, "r") as f:
                    file_contents = json.load(f)
                results["contents"].update(file_contents)

                for key in file_contents:
                    results["component_mapping"][key] = str(file)

        return results
