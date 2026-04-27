"""Tests for QuAM loading with TYPE_CHECKING forward references.

Covers the case where components use `from __future__ import annotations` +
`TYPE_CHECKING`-only imports to avoid circular imports (GitHub issue #90).

The Qubit / Resonator helpers in tests/serialisation/forward_ref_helpers/
simulate two real-world component modules that circularly reference each
other — a common pattern when building modular multi-file QuAM setups.
"""
import pytest
from quam import QuamRoot, quam_dataclass
from tests.serialisation.forward_ref_helpers.qubit import Qubit
from tests.serialisation.forward_ref_helpers.resonator import Resonator


@quam_dataclass
class Root(QuamRoot):
    qubit: Qubit
    resonator: Resonator


@pytest.fixture
def root():
    return Root(
        qubit=Qubit(resonator=Resonator(qubit="#../../")),
        resonator="#./qubit/resonator",
    )


class TestForwardRefSaving:
    """Saving should work regardless — these document the baseline."""

    def test_to_dict_does_not_raise(self, root):
        d = root.to_dict()
        assert "qubit" in d
        assert "resonator" in d

    def test_to_dict_nested_class_keys_present(self, root):
        d = root.to_dict()
        assert d["qubit"]["__class__"].endswith("Qubit")
        assert d["qubit"]["resonator"]["__class__"].endswith("Resonator")


class TestForwardRefLoading:
    """Loading must work when nested dicts carry __class__ keys."""

    def test_load_root_with_forward_ref_components(self):
        d = {
            "qubit": {
                "resonator": {
                    "qubit": "#../../",
                    "__class__": "tests.serialisation.forward_ref_helpers.resonator.Resonator",
                },
                "__class__": "tests.serialisation.forward_ref_helpers.qubit.Qubit",
            },
            "resonator": "#./qubit/resonator",
        }
        root = Root.load(d)
        assert isinstance(root.qubit, Qubit)
        assert isinstance(root.qubit.resonator, Resonator)

    def test_load_preserves_reference_strings(self):
        d = {
            "qubit": {
                "resonator": {
                    "qubit": "#../../",
                    "__class__": "tests.serialisation.forward_ref_helpers.resonator.Resonator",
                },
                "__class__": "tests.serialisation.forward_ref_helpers.qubit.Qubit",
            },
            "resonator": "#./qubit/resonator",
        }
        root = Root.load(d)
        assert root.get_raw_value("resonator") == "#./qubit/resonator"
        assert root.qubit.resonator.get_raw_value("qubit") == "#../../"


class TestForwardRefRoundtrip:
    """Full save → load roundtrip for circularly-referencing components."""

    def test_roundtrip_instances(self, root):
        d = root.to_dict()
        loaded = Root.load(d)

        assert isinstance(loaded.qubit, Qubit)
        assert isinstance(loaded.qubit.resonator, Resonator)

    def test_roundtrip_dict_equals_original(self, root):
        d = root.to_dict()
        loaded = Root.load(d)
        assert loaded.to_dict() == d


class TestForwardRefCollections:
    """Dict[str, ForwardRef] and List[ForwardRef] roundtrips."""

    def test_dict_of_forward_ref_roundtrip(self):
        from tests.serialisation.forward_ref_helpers.qubit_collection import (
            QubitCollection,
        )

        @quam_dataclass
        class CollectionRoot(QuamRoot):
            collection: QubitCollection

        obj = CollectionRoot(
            collection=QubitCollection(
                resonator_dict={"r1": Resonator(qubit="#../../../")}
            )
        )
        d = obj.to_dict()
        loaded = CollectionRoot.load(d)
        assert isinstance(loaded.collection.resonator_dict["r1"], Resonator)
        assert loaded.to_dict() == d

    def test_list_of_forward_ref_roundtrip(self):
        from tests.serialisation.forward_ref_helpers.qubit_collection import (
            QubitCollection,
        )

        @quam_dataclass
        class CollectionRoot(QuamRoot):
            collection: QubitCollection

        obj = CollectionRoot(
            collection=QubitCollection(
                resonator_list=[Resonator(qubit="#../../../")]
            )
        )
        d = obj.to_dict()
        loaded = CollectionRoot.load(d)
        assert isinstance(loaded.collection.resonator_list[0], Resonator)
        assert loaded.to_dict() == d
