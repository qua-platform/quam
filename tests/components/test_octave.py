from copy import deepcopy

from quam.components.octave import Octave, OctaveUpConverter, OctaveDownConverter
from quam.core.qua_config_template import qua_config_template
from quam.core.quam_classes import QuamRoot, quam_dataclass


@quam_dataclass
class OctaveQuAM(QuamRoot):
    octave: Octave


def test_instantiate_octave():
    octave = Octave(name="octave1")
    assert octave.RF_outputs == {}
    assert octave.IF_outputs == {}
    assert octave.loopbacks == []


def test_instantiate_octave_default_connectivity():
    octave = Octave()
    octave.initialize_default_connectivity()

    assert list(octave.RF_outputs) == [1, 2, 3, 4, 5]


def test_empty_octave_config():
    octave = Octave(name="octave1")
    machine = OctaveQuAM(octave=octave)
    config = machine.generate_config()

    expected_cfg = deepcopy(qua_config_template)
    expected_cfg["octaves"] = {
        "octave1": {
            "RF_outputs": {},
            "IF_outputs": {},
            "loopbacks": [],
        }
    }

    assert config == expected_cfg
