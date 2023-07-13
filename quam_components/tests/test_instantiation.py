import json
from typing import List

from quam_components.core import QuamBase
from quam_components.components.superconducting_qubits import Transmon

quam_dict_single = """
{
    "qubit": {
        "id": 0,
        "xy": {
            "pi_amp": 10e-3,
            "pi_length": 40,
            "anharmonicity": 200e6
        }
    }
}
"""

class QuamTestSingle(QuamBase):
    qubit: Transmon


def test_instantiation_single_element():
    quam = QuamTestSingle()
    quam.instantiate_contents(quam_dict_single)


# quam_dict = """
# {
#     "qubits": [
#         {
#             "id": 0,
#             "xy": {
#                 "pi_amp": 10e-3,
#                 "pi_length": 40,
#                 "anharmonicity": 200e6
#             }
#         }
#     ]
# }
# """

# class QuamTest(QuamBase):
#     qubits: List[Transmon]