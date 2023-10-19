from pathlib import Path
import json

from quam.components import *
from quam.components.channels import IQChannel, InOutIQChannel, SingleChannel
from quam.core import QuamRoot


def create_quam_superconducting_referenced(num_qubits: int) -> QuamRoot:
    """Create a QuAM with a number of qubits.

    Args:
        num_qubits (int): Number of qubits to create.

    Returns:
        QuamRoot: A QuAM with the specified number of qubits.
    """
    quam = QuAM()
    quam.wiring = {
        "qubits": [
            {
                "port_I": ("con1", 5 * k + 3),
                "port_Q": ("con1", 5 * k + 4),
                "port_Z": ("con1", 5 * k + 5),
            }
            for k in range(num_qubits)
        ],
        "resonator": {
            "output_port_I": ("con1", 1),
            "output_port_Q": ("con1", 2),
            "input_port_I": ("con1", 1),
            "input_port_Q": ("con1", 2),
        },
    }

    for idx in range(num_qubits):
        # Create qubit components
        transmon = Transmon(
            id=idx,
            xy=IQChannel(
                mixer=Mixer(),
                output_port_I=f"#/wiring/qubits/{idx}/port_I",
                output_port_Q=f"#/wiring/qubits/{idx}/port_Q",
                local_oscillator=LocalOscillator(power=10, frequency=6e9),
                intermediate_frequency=100e6,
            ),
            z=SingleChannel(output_port=f"#/wiring/qubits/{idx}/port_Z"),
        )
        quam.qubits.append(transmon)
        quam.local_oscillators.append(f"#/qubits/{idx}/xy/local_oscillator")
        quam.mixers.append(f"#/qubits/{idx}/xy/mixer")

        readout_resonator = InOutIQChannel(
            id=idx,
            output_port_I="#/wiring/resonator/output_port_I",
            output_port_Q="#/wiring/resonator/output_port_Q",
            input_port_I="#/wiring/resonator/input_port_I",
            input_port_Q="#/wiring/resonator/input_port_Q",
            mixer=Mixer(),
            local_oscillator=LocalOscillator(power=10, frequency=6e9),
        )
        quam.resonators.append(readout_resonator)
        quam.local_oscillators.append(f"#/resonators/{idx}/xy/local_oscillator")
        quam.mixers.append(f"#/resonators/{idx}/xy/mixer")
    return quam


if __name__ == "__main__":
    folder = Path("quam-components/quam/examples/quam_superconducting_referenced")
    folder.mkdir(exist_ok=True)

    quam = create_quam_superconducting_referenced(num_qubits=3)
    quam.save(folder / "quam", content_mapping={"wiring.json": "wiring"})

    qua_file = folder / "qua_config.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)

    quam_loaded = QuAM.load(folder / "quam")

    qua_file = folder / "qua_config2.json"
    qua_config = quam.generate_config()
    json.dump(qua_config, qua_file.open("w"), indent=4)
