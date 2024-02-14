from quam.utils import get_class_from_path


def test_get_transmon_from_class_path():
    transmon_path = "quam.examples.superconducting_qubits.components.Transmon"
    transmon_class = get_class_from_path(transmon_path)
    from quam.examples.superconducting_qubits.components import Transmon

    assert transmon_class == Transmon
