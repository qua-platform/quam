import pytest
from quam.core.quam_classes import quam_dataclass
from quam.components import Qubit
from quam.components.macro import QubitMacro


@quam_dataclass
class TestMacro(QubitMacro):
    """Simple macro class for testing purposes"""

    def apply(self, *args, **kwargs):
        # Return inputs to verify they were passed correctly
        return (self.qubit, args, kwargs)


@pytest.fixture
def test_qubit():
    """Fixture providing a qubit with common test macros"""
    qubit = Qubit(id="test_qubit")

    # Add some common macros
    qubit.macros["x_gate"] = TestMacro()
    qubit.macros["test_op"] = TestMacro()

    return qubit
