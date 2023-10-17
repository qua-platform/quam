from quam.utils import get_class_from_path


def test_get_transmon():
    transmon_path = "quam.components.superconducting_qubits.Transmon"
    transmon_class = get_class_from_path(transmon_path)
    from quam.components.superconducting_qubits import Transmon

    assert transmon_class == Transmon
