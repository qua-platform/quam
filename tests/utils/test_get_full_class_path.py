from quam.core import *
from quam.utils import get_full_class_path


def test_get_transmon_class_path():
    from quam.examples.superconducting_qubits.components import Transmon

    class_path = get_full_class_path(Transmon)
    assert class_path == "quam.examples.superconducting_qubits.components.Transmon"


@quam_dataclass
class QuamComponentTest(QuamComponent):
    str_val: str


def test_get_local_class_path():
    class_path = get_full_class_path(QuamComponentTest)
    assert class_path == "test_get_full_class_path.QuamComponentTest"
