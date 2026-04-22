"""Tests for QuAM loading with TYPE_CHECKING forward references.

Covers the case where components use `from __future__ import annotations` +
`TYPE_CHECKING`-only imports to avoid circular imports (GitHub issue #90).

The Qubit / Resonator helpers in quam/components/helper_files/ simulate two
real-world component modules that circularly reference each other — a common
pattern when building modular multi-file QuAM setups.
"""
from quam import QuamRoot, quam_dataclass
from quam.components.helper_files.qubit import Qubit
from quam.components.helper_files.resonator import Resonator


@quam_dataclass
class Root(QuamRoot):
    qubit: Qubit
    resonator: Resonator


class TestForwardRefSaving:
    """Saving should work regardless — these document the baseline."""

    def test_to_dict_does_not_raise(self):
        root = Root(
            qubit=Qubit(resonator=Resonator(qubit="#../../")),
            resonator="#./qubit/resonator",
        )
        d = root.to_dict()
        assert "qubit" in d
        assert "resonator" in d

    def test_to_dict_nested_class_keys_present(self):
        root = Root(
            qubit=Qubit(resonator=Resonator(qubit="#../../")),
            resonator="#./qubit/resonator",
        )
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
                    "__class__": "quam.components.helper_files.resonator.Resonator",
                },
                "__class__": "quam.components.helper_files.qubit.Qubit",
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
                    "__class__": "quam.components.helper_files.resonator.Resonator",
                },
                "__class__": "quam.components.helper_files.qubit.Qubit",
            },
            "resonator": "#./qubit/resonator",
        }
        root = Root.load(d)
        assert root.get_raw_value("resonator") == "#./qubit/resonator"
        assert root.qubit.resonator.get_raw_value("qubit") == "#../../"


class TestForwardRefRoundtrip:
    """Full save → load roundtrip for circularly-referencing components."""

    def test_roundtrip_instances(self):
        original = Root(
            qubit=Qubit(resonator=Resonator(qubit="#../../")),
            resonator="#./qubit/resonator",
        )
        d = original.to_dict()
        loaded = Root.load(d)

        assert isinstance(loaded.qubit, Qubit)
        assert isinstance(loaded.qubit.resonator, Resonator)

    def test_roundtrip_dict_equals_original(self):
        original = Root(
            qubit=Qubit(resonator=Resonator(qubit="#../../")),
            resonator="#./qubit/resonator",
        )
        d = original.to_dict()
        loaded = Root.load(d)
        assert loaded.to_dict() == d
