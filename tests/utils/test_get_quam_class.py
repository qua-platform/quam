from quam.core.utils import get_quam_class


def test_get_transmon():
    transmon_path = "quam.components.superconducting_qubits.Transmon"
    transmon_class = get_quam_class(transmon_path)
    from quam.components.superconducting_qubits import Transmon

    assert transmon_class == Transmon
