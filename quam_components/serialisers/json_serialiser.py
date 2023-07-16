from typing import Union, Dict
from pathlib import Path
import json

from quam_components.core import QuamBase, QuamComponent


class AbstractSerialiser:
    def save(
        self,
        path: Union[Path, str],
        quam_obj: Union[QuamBase, QuamComponent],
        component_mapping: Dict[str, str] = None,
    ):
        raise NotImplementedError

    def load(
        self,
        path: Union[Path, str] = None,
    ):
        raise NotImplementedError
    

class JSONSerialiser(AbstractSerialiser):
    def save(
        self,
        path: Union[Path, str],
        quam_obj: Union[QuamBase, QuamComponent],
        component_mapping: Dict[str, str] = None,
    ):
        
        

    def load(
        self,
        path: Union[Path, str] = None,
    ):
        path = Path(path)
        component_mapping = {}

        if not path.exists():
            raise FileNotFoundError(f"Path {path} not found, cannot load JSON.")

        if path.is_file():
            if not path.suffix == '.json':
                raise TypeError(f"File {path} is not a JSON file.")
            with open(path, "r") as f:
                contents = json.load(f)
        elif path.is_dir():
            contents = {}
            for file in path.iterdir():
                if not file.suffix == '.json':
                    continue

                with open(file, "r") as f:
                    file_contents = json.load(f)
                contents.update(file_contents)
                for key in file_contents:
                    component_mapping[key] = str(file)

        return contents, component_mapping