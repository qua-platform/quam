"""Test for include_defaults_in_serialization config field."""

import pytest
from quam.config.resolvers import get_quam_config


def test_include_defaults_config_field_defaults_to_true():
    """Test that include_defaults_in_serialization defaults to True."""
    config = get_quam_config()
    assert hasattr(config, "include_defaults_in_serialization")
    assert config.include_defaults_in_serialization is True


def test_include_defaults_config_version_3():
    """Test that config version is bumped to 3."""
    config = get_quam_config()
    assert config.version == 3


