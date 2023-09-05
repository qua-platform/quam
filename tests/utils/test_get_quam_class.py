from quam_components.core.utils import get_quam_class


def test_get_transmon():
    transmon_path = "quam_components.components.superconducting_qubits.Transmon"
    transmon_class = get_quam_class(transmon_path)
    from quam_components.components.superconducting_qubits import Transmon

    assert transmon_class == Transmon
