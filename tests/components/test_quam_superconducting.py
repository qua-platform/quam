from quam.components.superconducting_qubits import QuAM
from quam.examples.generate_superconducting_quam import *
from quam.components import *
from quam.core import *


def test_create_quam_superconducting_referenced_generate_config():
    quam = create_quam_superconducting_referenced(num_qubits=2)
    assert isinstance(quam.wiring, QuamDict)

    assert hasattr(quam.wiring.qubits[0], "port_I")

    quam.generate_config()
    # print(quam.qubits[0].xy.mixer.port_I)
    # assert quam.qubits[0].xy.mixer.port_I == 1
    # assert quam.qubits[0].xy.mixer.port_Q == 2


def test_quam_superconducting_referenced(tmp_path):
    folder = tmp_path / "quam_superconducting_referenced"
    folder.mkdir(exist_ok=True)
    quam = create_quam_superconducting_referenced(num_qubits=3)

    quam.qubits[0].to_dict()
    quam.save(folder / "quam")


def test_quam_referenced_full(tmp_path):
    folder = tmp_path / "quam_superconducting_referenced"
    folder.mkdir(exist_ok=True)

    quam = create_quam_superconducting_referenced(num_qubits=3)
    quam.save(folder / "quam", content_mapping={"wiring.json": "wiring"})

    loaded_quam = json.load((folder / "quam" / "state.json").open("r"))
    assert set(loaded_quam.keys()) == set(
        [
            "qubits",
            "resonators",
            "mixers",
            "local_oscillators",
            "__class__",
        ]
    )
    assert loaded_quam["__class__"] == "quam.components.superconducting_qubits.QuAM"
    assert len(loaded_quam["qubits"]) == 3
    assert len(loaded_quam["mixers"]) == 6
    assert len(loaded_quam["local_oscillators"]) == 6
    assert loaded_quam["mixers"][0] == "#/qubits/0/xy/mixer"
    assert loaded_quam["local_oscillators"][0] == "#/qubits/0/xy/local_oscillator"
    assert loaded_quam["qubits"][0]["xy"]["opx_output_I"] == "#/wiring/qubits/0/port_I"
    assert loaded_quam["qubits"][0]["xy"]["intermediate_frequency"] == 100e6

    loaded_quam = json.load((folder / "quam" / "wiring.json").open("r"))
    assert set(loaded_quam.keys()) == set(["wiring"])
    assert len(loaded_quam["wiring"]["qubits"]) == 3
    assert loaded_quam["wiring"]["qubits"][0]["port_I"] == [
        "con1",
        3,
    ]  # transformed to tuple

    qua_file = folder / "qua_config.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)
    qua_config_str = json.dumps(qua_config, indent=4)

    quam_loaded = QuAM.load(folder / "quam")
    assert quam.get_attrs().keys() == quam_loaded.get_attrs().keys()

    qua_file = folder / "qua_config2.json"
    qua_config2 = quam.generate_config()
    qua_config2_str = json.dumps(qua_config2, indent=4)

    assert qua_config_str == qua_config2_str
