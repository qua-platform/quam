import pytest
from qm import qua
from quam.utils.pulse import add_amplitude_scale_to_pulse_name


def test_add_amplitude_scale_none():
    """Test that when amplitude_scale is None, pulse_name is returned unchanged."""
    with qua.program():
        result = add_amplitude_scale_to_pulse_name("test_pulse", None)
        assert result == "test_pulse"


def test_add_amplitude_scale_scalar_value():
    """Test that scalar amplitude_scale creates qua.amp with single value."""
    with qua.program():
        result = add_amplitude_scale_to_pulse_name("test_pulse", 0.5)
        # Result should be a tuple (pulse_name, amp_tuple)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "test_pulse"


def test_add_amplitude_scale_qua_variable():
    """Test that QUA variable amplitude_scale works correctly."""
    with qua.program():
        amp_var = qua.declare(qua.fixed)
        result = add_amplitude_scale_to_pulse_name("test_pulse", amp_var)
        # Result should be a tuple (pulse_name, amp_tuple)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "test_pulse"


def test_add_amplitude_scale_sequence():
    """Test that sequence of values creates qua.amp with unpacked values."""
    with qua.program():
        result = add_amplitude_scale_to_pulse_name("test_pulse", [0.1, 0.2, 0.3, 0.4])
        # Result should be a tuple (pulse_name, amp_tuple) with 4 elements in amp_tuple
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "test_pulse"
        assert len(result[1]) == 4  # 4 amplitude values


def test_add_amplitude_scale_mixed_sequence():
    """Test that sequence with mixed scalar and QUA variable elements works."""
    with qua.program():
        amp_var = qua.declare(qua.fixed)
        result = add_amplitude_scale_to_pulse_name(
            "test_pulse", [0.1, 0.2, amp_var, 0.4]
        )
        # Result should be a tuple (pulse_name, amp_tuple) with 4 elements including QUA var
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "test_pulse"
        assert len(result[1]) == 4  # 4 amplitude values (3 scalars + 1 QUA var)


def test_add_amplitude_scale_invalid_type():
    """Test that invalid amplitude_scale type raises ValueError."""
    with qua.program():
        with pytest.raises(ValueError, match="Invalid amplitude scale"):
            add_amplitude_scale_to_pulse_name("test_pulse", "invalid")
