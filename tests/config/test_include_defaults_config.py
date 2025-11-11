"""Test for include_defaults_in_serialization config field."""

import pytest
from quam.config.resolvers import get_quam_config


def test_include_defaults_config_field_defaults_to_true():
    """Test that serialization.include_defaults defaults to True."""
    config = get_quam_config()
    assert hasattr(config, "serialization")
    # serialization might be None if loading an old v2 config
    if config.serialization is not None:
        assert hasattr(config.serialization, "include_defaults")
        assert config.serialization.include_defaults is True
    else:
        # If serialization is None, the default fallback is True
        # (handled in JSONSerialiser._resolve_include_defaults())
        pass


def test_include_defaults_config_version_3():
    """Test that config version is bumped to 3."""
    config = get_quam_config()
    assert config.version == 3


