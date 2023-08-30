# QuAM Components


## Installation instructions (Mac)
From the root folder run the following commands in terminal

```
python3 -m venv venv-quam
source venv-quam/bin/activate
pip install poetry
poetry install --with dev
```

## Limitations
### Dictionary limitations
Dictionaries are currently treated as simple dictionary objects.
As such, they cannot contain references.
They also cannot contain QuAM components because the serialisation isn't handled properly
#### Dictionaries cannot contain QuAM components
The following code cannot be serialised properly:
```Python
@dataclass
class CustomComponent(QuamComponent):
    mixers: Dict[int, Mixer]

mixer = Mixer()
custom_component = CustomComponent(mixers={0: mixer})
```
This feature will be implemented in the future.