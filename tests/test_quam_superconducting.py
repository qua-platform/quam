from quam_components.examples.generate_quam import *


def test_create_quam_superconducting_simple():
    quam = create_quam_superconducting_simple(num_qubits=2)

    assert len(quam.qubits) == 2
    assert len(quam.resonators) == 2
    assert len(quam.mixers) == 4
    assert len(quam.local_oscillators) == 4
    assert len(list(quam.iterate_quam_components())) == 16  # Includes XY and Z channels


def test_create_quam_superconducting_simple_build_config():
    quam = create_quam_superconducting_simple(num_qubits=2)
    qua_config = quam.build_config()
