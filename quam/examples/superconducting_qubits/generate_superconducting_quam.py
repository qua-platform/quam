from pathlib import Path
import json

from quam.components import *
from quam.components.channels import IQChannel, InOutIQChannel, SingleChannel
from quam.examples.superconducting_qubits.components import Transmon, Quam
from quam.core import QuamRoot


def create_quam_superconducting_referenced(num_qubits: int) -> QuamRoot:
    """Create a QUAM with a number of qubits.

    Args:
        num_qubits (int): Number of qubits to create.

    Returns:
        QuamRoot: A QUAM with the specified number of qubits.
    """
    machine = Quam()
    def _qubit_port(idx, offset):
        # FEM 1 ports 1-2 reserved for feedline; qubits start at FEM 1 port 3.
        # Each LF FEM has 8 outputs, so qubits 0-1 fit on FEM 1, qubit 2+ overflow to FEM 2+.
        flat = idx * 3 + offset
        fem1_qubit_ports = 6  # ports 3-8 on FEM 1
        if flat < fem1_qubit_ports:
            return ("con1", 1, flat + 3)
        rem = flat - fem1_qubit_ports
        return ("con1", 2 + rem // 8, rem % 8 + 1)

    machine.wiring = {
        "qubits": {
            f"q{idx}": {
                "port_I": _qubit_port(idx, 0),
                "port_Q": _qubit_port(idx, 1),
                "port_Z": _qubit_port(idx, 2),
            }
            for idx in range(num_qubits)
        },
        "feedline": {
            "opx_output_I": ("con1", 1, 1),
            "opx_output_Q": ("con1", 1, 2),
            "opx_input_I": ("con1", 1, 1),
            "opx_input_Q": ("con1", 1, 2),
        },
    }

    for idx in range(num_qubits):
        # Create qubit components
        transmon = Transmon(id=idx)
        machine.qubits[transmon.name] = transmon

        transmon.xy = IQChannel(
            opx_output_I=f"#/wiring/qubits/q{idx}/port_I",
            opx_output_Q=f"#/wiring/qubits/q{idx}/port_Q",
            frequency_converter_up=FrequencyConverter(
                mixer=Mixer(),
                local_oscillator=LocalOscillator(power=10, frequency=6e9),
            ),
            intermediate_frequency=100e6,
        )

        transmon.z = SingleChannel(opx_output=f"#/wiring/qubits/q{idx}/port_Z")

        transmon.resonator = InOutIQChannel(
            id=idx,
            opx_output_I="#/wiring/feedline/opx_output_I",
            opx_output_Q="#/wiring/feedline/opx_output_Q",
            opx_input_I="#/wiring/feedline/opx_input_I",
            opx_input_Q="#/wiring/feedline/opx_input_Q",
            frequency_converter_up=FrequencyConverter(
                mixer=Mixer(), local_oscillator=LocalOscillator(power=10, frequency=6e9)
            ),
            intermediate_frequency=100e6,
        )
    return machine


if __name__ == "__main__":
    folder = Path(__file__).parent / "quam_superconducting_referenced"
    folder.mkdir(exist_ok=True)

    quam = create_quam_superconducting_referenced(num_qubits=3)
    quam.save(folder / "quam", content_mapping={"wiring": "wiring.json"})

    qua_file = folder / "qua_config.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)

    quam_loaded = Quam.load(folder / "quam")

    qua_file = folder / "qua_config2.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)
