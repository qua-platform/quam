from quam_components.examples.generate_superconducting_quam import *


def test_create_quam_superconducting_simple():
    quam = create_quam_superconducting_simple(num_qubits=2)

    assert len(quam.qubits) == 2
    assert len(quam.resonators) == 2
    assert len(quam.mixers) == 4
    assert len(quam.local_oscillators) == 4

    assert len(list(quam.iterate_quam_components())) == 17  # Includes XY and Z channels


def test_create_quam_superconducting_simple_build_config():
    quam = create_quam_superconducting_simple(num_qubits=2)
    qua_config = quam.build_config()
    assert isinstance(qua_config, dict)


def test_create_quam_superconducting_simple_build_config():
    quam = create_quam_superconducting_referenced(num_qubits=2)

    assert hasattr(quam.wiring.qubits[0], "port_I")

    qua_config = quam.build_config()
    print(quam.qubits[0].xy.mixer.port_I)
    assert quam.qubits[0].xy.mixer.port_I == 0
    assert quam.qubits[0].xy.mixer.port_Q == 1

def test_quam_superconducting_referenced(tmp_path):
    folder = tmp_path / "quam_superconducting_referenced"
    folder.mkdir(exist_ok=True)
    quam = create_quam_superconducting_referenced(num_qubits=3)

    quam.qubits[0].to_dict()
    quam.save(folder / "quam")
