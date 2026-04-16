from typing import Dict, Any
import pytest
from quam.components.channels import SingleChannel, Channel
from quam.components.quantum_components.qubit import Qubit
from quam.components.quantum_components.quantum_component import QuantumComponent
from quam.core import quam_dataclass, QuamRoot
from quam.components.ports import LFFEMAnalogOutputPort
from quam.components.pulses import Pulse

@quam_dataclass
class HybridChannelFirst(SingleChannel, Qubit):
    """Hybrid class where Channel comes first in MRO."""
    pass


@quam_dataclass
class HybridQubitFirst(Qubit, SingleChannel):
    """Hybrid class where Qubit comes first in MRO."""
    pass


def test_hybrid_channel_first_instantiation(qua_config):
    """Test instantiation of HybridChannelFirst (Channel logic dominates)."""
    hybrid = HybridChannelFirst(
        id="test_c1",
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1)
    )

    # Check MRO-based defaults/logic
    # Channel.name implementation: if id is str, return id.
    assert hybrid.name == "test_c1"
    assert hybrid.id == "test_c1"

    # Check config generation
    hybrid.apply_to_config(qua_config)

    assert "test_c1" in qua_config["elements"]
    assert "singleInput" in qua_config["elements"]["test_c1"]

    # Check that it is recognized as both
    assert isinstance(hybrid, Channel)
    assert isinstance(hybrid, QuantumComponent)
    assert isinstance(hybrid, Qubit)


def test_hybrid_qubit_first_instantiation(qua_config):
    """Test instantiation of HybridQubitFirst (Qubit logic dominates)."""
    hybrid = HybridQubitFirst(
        id="test_q1",
        opx_output=LFFEMAnalogOutputPort("con1", 1, 2)
    )

    # Qubit.name implementation: if id is str, return id.
    assert hybrid.name == "test_q1"

    # Config generation should still work via SingleChannel.apply_to_config
    hybrid.apply_to_config(qua_config)

    assert "test_q1" in qua_config["elements"]
    assert "singleInput" in qua_config["elements"]["test_q1"]


def test_hybrid_int_id_naming():
    """Test naming behavior with integer IDs."""
    
    # Channel first: defaults to "ch{id}"
    h1 = HybridChannelFirst(
        id=1,
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1)
    )
    # Channel._default_label is "ch"
    assert h1.name == "ch1"
    
    # Qubit first: defaults to "q{id}"
    h2 = HybridQubitFirst(
        id=2,
        opx_output=LFFEMAnalogOutputPort("con1", 1, 2)
    )
    # Qubit logic
    assert h2.name == "q2"


def test_hybrid_with_root_config():
    """Test full config generation within a QuamRoot."""
    @quam_dataclass
    class MyRoot(QuamRoot):
        component: HybridChannelFirst

    root = MyRoot(
        component=HybridChannelFirst(
            id=1,
            opx_output=LFFEMAnalogOutputPort("con1", 1, 1)
        )
    )
    
    config = root.generate_config()
    assert "ch1" in config["elements"]
    assert config["elements"]["ch1"]["singleInput"]["port"] == ("con1", 1, 1)


def test_conflicting_defaults():
    """Verify handling of default values."""
    # Qubit has id default "#./inferred_id"
    # Channel has id default None
    
    # If Qubit is first, id default should be "#./inferred_id"
    h_q = HybridQubitFirst(opx_output=LFFEMAnalogOutputPort("con1", 1, 1))
    assert h_q.id == "#./inferred_id"
    
    # If Channel is first, id default should be None
    h_c = HybridChannelFirst(opx_output=LFFEMAnalogOutputPort("con1", 1, 1))
    assert h_c.id is None

def test_qubit_get_pulse_on_hybrid():
    """Test if Qubit.get_pulse works when the pulse is on the hybrid object itself."""
    from quam.components.pulses import SquarePulse
    pulse = SquarePulse(length=100, amplitude=0.5)
    hybrid = HybridChannelFirst(
        id="test_c1",
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1),
        operations={"readout": pulse}
    )

    # Qubit.get_pulse iterates over self.channels.
    # If self.channels doesn't include self, this will fail.
    try:
        found_pulse = hybrid.get_pulse("readout")
        assert found_pulse is pulse
    except ValueError as e:
        pytest.fail(f"Qubit.get_pulse failed to find pulse on hybrid object: {e}")


def test_hybrid_channels_dict_key_matches_name():
    """Verify that when a Qubit is a Channel, channels dict uses self.name as key."""
    from quam.components.pulses import SquarePulse

    # Test with HybridChannelFirst and string ID
    hybrid_cf = HybridChannelFirst(
        id="test_channel",
        opx_output=LFFEMAnalogOutputPort("con1", 1, 1),
        operations={"readout": SquarePulse(length=100, amplitude=0.5)}
    )
    assert hybrid_cf.name == "test_channel"
    assert hybrid_cf.name in hybrid_cf.channels
    assert hybrid_cf.channels[hybrid_cf.name] is hybrid_cf

    # Test with HybridQubitFirst and string ID
    hybrid_qf = HybridQubitFirst(
        id="test_qubit",
        opx_output=LFFEMAnalogOutputPort("con1", 1, 2),
        operations={"readout": SquarePulse(length=100, amplitude=0.5)}
    )
    assert hybrid_qf.name == "test_qubit"
    assert hybrid_qf.name in hybrid_qf.channels
    assert hybrid_qf.channels[hybrid_qf.name] is hybrid_qf

    # Test with HybridChannelFirst and integer ID
    hybrid_cf_int = HybridChannelFirst(
        id=5,
        opx_output=LFFEMAnalogOutputPort("con1", 1, 3),
    )
    assert hybrid_cf_int.name == "ch5"
    assert hybrid_cf_int.name in hybrid_cf_int.channels
    assert hybrid_cf_int.channels[hybrid_cf_int.name] is hybrid_cf_int

    # Test with HybridQubitFirst and integer ID
    hybrid_qf_int = HybridQubitFirst(
        id=7,
        opx_output=LFFEMAnalogOutputPort("con1", 1, 4),
    )
    assert hybrid_qf_int.name == "q7"
    assert hybrid_qf_int.name in hybrid_qf_int.channels
    assert hybrid_qf_int.channels[hybrid_qf_int.name] is hybrid_qf_int
