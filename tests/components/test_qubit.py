from quam.components import Qubit


def test_qubit_name_int():
    qubit = Qubit(id=0)
    assert qubit.name == "q0"


def test_qubit_name_str():
    qubit = Qubit(id="qubit0")
    assert qubit.name == "qubit0"
