import pytest
from copy import deepcopy

from quam_components.core.quam_base import QuamBase
from quam_components.components.superconducting_qubits import Transmon


quam_dict_single = {
    "qubit": {
        "id": 0,
        # "xy": {
        #     "pi_amp": 10e-3,
        #     "pi_length": 40,
        #     "anharmonicity": 200e6,
        # }
    },
}


class QuamTestSingle(QuamBase):
    qubit: Transmon


def test_instantiation_single_element():
    quam = QuamTestSingle()
    quam.load(quam_dict_single)

    assert isinstance(quam.qubit, Transmon)
    assert quam.qubit.id == 0
    assert quam.qubit.xy is None


quam_dict_single_nested = {
    "qubit": {
        "id": 0,
        "xy": {
            "pi_amp": 10e-3,
            "pi_length": 40,
            "anharmonicity": 200e6,
        }
    },
}


def test_instantiation_single_nested_element():
    quam = QuamTestSingle()
    with pytest.raises(AttributeError):
        quam.load(quam_dict_single_nested)

    quam_dict = deepcopy(quam_dict_single_nested)
    quam_dict['qubit']['xy']['mixer'] = {
        "name": "mixer", 
        "local_oscillator": {"power": 10, "frequency": 6e9}
    }
    quam.load(quam_dict)

    assert quam.qubit.xy.mixer.name == "mixer"
    assert quam.qubit.xy.mixer.local_oscillator.power == 10
    assert quam.qubit.xy.mixer.local_oscillator.frequency == 6e9


def test_instantiation_fixed_attrs():
    ...

def test_instantiation_unfixed_attrs():
    ...

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