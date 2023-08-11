from quam_components.examples.generate_superconducting_quam import *


def test_create_quam_superconducting_simple():
    quam = create_quam_superconducting_simple(num_qubits=2)

    assert len(quam.qubits) == 2
    assert len(quam.resonators) == 2
    assert len(quam.mixers) == 4
    assert len(quam.local_oscillators) == 4

    assert len(list(quam.iterate_components())) == 19  # Includes XY and Z channels


def test_create_quam_superconducting_simple_build_config():
    quam = create_quam_superconducting_simple(num_qubits=2)
    qua_config = quam.build_config()
    assert isinstance(qua_config, dict)


def test_create_quam_superconducting_referenced_build_config():
    quam = create_quam_superconducting_referenced(num_qubits=2)

    assert hasattr(quam.wiring.qubits[0], "port_I")

    qua_config = quam.build_config()
    print(quam.qubits[0].xy.mixer.port_I)
    assert quam.qubits[0].xy.mixer.port_I == 1
    assert quam.qubits[0].xy.mixer.port_Q == 2


def test_quam_superconducting_referenced(tmp_path):
    folder = tmp_path / "quam_superconducting_referenced"
    folder.mkdir(exist_ok=True)
    quam = create_quam_superconducting_referenced(num_qubits=3)

    d = quam.qubits[0].to_dict()
    quam.save(folder / "quam")


def test_quam_referenced_full(tmp_path):
    folder = tmp_path / "quam_superconducting_referenced"
    folder.mkdir(exist_ok=True)

    quam = create_quam_superconducting_referenced(num_qubits=3)
    quam.save(folder / "quam", content_mapping={"wiring.json": "wiring"})

    loaded_quam = json.load((folder / "quam" / "state.json").open("r"))
    assert set(loaded_quam.keys()) == set(
        ["qubits", "resonators", "mixers", "local_oscillators", "analog_inputs"]
    )
    assert len(loaded_quam["qubits"]) == 3
    assert len(loaded_quam["resonators"]) == 3
    assert len(loaded_quam["mixers"]) == 6
    assert len(loaded_quam["local_oscillators"]) == 6
    assert loaded_quam["qubits"][0]["xy"]["mixer"] == ":mixers[0]"
    assert loaded_quam["mixers"][0]["local_oscillator"] == ":local_oscillators[0]"
    assert loaded_quam["mixers"][0]["port_I"] == ":wiring.qubits[0].port_I"
    assert loaded_quam["mixers"][0]["frequency_drive"] == ":qubits[0].frequency_01"

    loaded_quam = json.load((folder / "quam" / "wiring.json").open("r"))
    assert set(loaded_quam.keys()) == set(["wiring"])
    assert len(loaded_quam["wiring"]["qubits"]) == 3
    assert len(loaded_quam["wiring"]["resonators"]) == 3
    assert loaded_quam["wiring"]["qubits"][0]["port_I"] == 1

    qua_file = folder / "qua_config.json"
    qua_config = quam.build_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)
    qua_config_str = json.dumps(qua_config, indent=4)

    quam_loaded = QuAM.load(folder / "quam")
    assert quam.get_attrs().keys() == quam_loaded.get_attrs().keys()

    qua_file = folder / "qua_config2.json"
    qua_config2 = quam.build_config()
    qua_config2_str = json.dumps(qua_config2, indent=4)

    assert qua_config_str == qua_config2_str


def test_quam_referenced_add_pulse(tmp_path):
    default_pulses = [
        f"{axis}{angle}" for axis in "XY" for angle in ["m90", "90", "180"]
    ]
    folder = tmp_path / "quam_superconducting_referenced"
    folder.mkdir(exist_ok=True)

    quam = create_quam_superconducting_referenced(num_qubits=3)
    quam.save(folder / "quam", content_mapping={"wiring.json": "wiring"})
    loaded_quam = json.load((folder / "quam" / "state.json").open("r"))
    assert "pulses" not in loaded_quam["qubits"][0]["xy"]

    quam.qubits[0].xy.pulses.append("X270")
    quam.save(folder / "quam", content_mapping={"wiring.json": "wiring"})
    loaded_quam = json.load((folder / "quam" / "state.json").open("r"))
    loaded_quam["qubits"][0]["xy"]["pulses"] == default_pulses + ["X270"]
