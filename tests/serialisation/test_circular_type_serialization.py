from quam import QuamRoot, quam_dataclass
from quam.components.helper_files.qubit import Qubit
from quam.components.helper_files.resonator import Resonator


@quam_dataclass
class Root(QuamRoot):
    qubit: Qubit
    resonator: Resonator


def test_circular_type_serialization():

    root = Root(
        qubit=Qubit(resonator=Resonator(qubit="#../../")),
        resonator="#./qubit/resonator",
    )

    # this fails with NameError: name 'Resonator' is not defined
    root.to_dict()
