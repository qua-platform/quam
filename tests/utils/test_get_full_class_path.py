from dataclasses import dataclass
from quam_components.core import *
from quam_components.core.utils import get_full_class_path


def test_get_transmon_class_path():
    from quam_components.components.superconducting_qubits import Transmon

    class_path = get_full_class_path(Transmon)
    assert class_path == "quam_components.components.superconducting_qubits.Transmon"


@dataclass
class TestQuamComponent(QuamComponent):
    str_val: str


def test_get_local_class_path():
    class_path = get_full_class_path(TestQuamComponent)
    assert class_path == "test_get_full_class_path.TestQuamComponent"
