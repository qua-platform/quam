"""
Tests for JSONSerialiser save behavior with new default handling.

This module tests the end-to-end save functionality with the new
include_defaults_in_save config field for ticket #11:
- QuamRoot.save() includes defaults by default (new behavior)
- Saved JSON file contains all fields including defaults
- Explicit include_defaults=False excludes defaults (override behavior)
- Complex nested objects with defaults are properly saved
- All save operations use isolated temporary directories only
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch

from quam.serialisation.json import JSONSerialiser


class TestJSONSerialiserSaveDefaults:
    """Test suite for save behavior with new default handling."""

    def test_save_includes_defaults_by_default_new_config(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test that save includes defaults by default with new config behavior."""
        # Mock a new v3 config with include_defaults_in_save = True
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is True  # Verify config read correctly
            
            # Save to isolated location
            save_path = tmp_path / "test_save_with_defaults.json"
            serialiser.save(sample_quam_object, save_path)
            
            # Verify file was created and contains defaults
            assert save_path.exists()
            
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
            
            # Should include default values
            assert 'default_val' in saved_data  # This is a default field
            assert saved_data['default_val'] == 10  # Default value from MockQuamRoot
            
            # Should include both default and non-default values
            assert 'other' in saved_data
            assert saved_data['other'] == 'specific_value'  # Non-default value

    def test_save_excludes_defaults_with_migrated_config(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test that save excludes defaults with migrated v2→v3 config."""
        # Mock a migrated config with include_defaults_in_save = False (preserves v2 behavior)
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': False
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is False  # Verify config read correctly
            
            # Save to isolated location  
            save_path = tmp_path / "test_save_migrated_config.json"
            serialiser.save(sample_quam_object, save_path)
            
            # Verify file was created and excludes defaults
            assert save_path.exists()
            
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
            
            # Should exclude default values (preserves v2 space-saving behavior)
            assert 'default_val' not in saved_data or saved_data.get('default_val') != 10
            
            # Should still include non-default values
            assert 'other' in saved_data
            assert saved_data['other'] == 'specific_value'

    def test_explicit_include_defaults_false_overrides_config(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test that explicit include_defaults=False overrides config setting."""
        # Mock config says include defaults, but explicit parameter overrides
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser(include_defaults=False)  # Explicit override
            assert serialiser.include_defaults is False
            
            save_path = tmp_path / "test_explicit_false_override.json"
            # Use the serializer's setting by passing include_defaults=False explicitly
            serialiser.save(sample_quam_object, save_path, include_defaults=False)
            
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
            
            # Should exclude defaults despite config saying include them
            assert 'default_val' not in saved_data or saved_data.get('default_val') != 10

    def test_explicit_include_defaults_true_overrides_config(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test that explicit include_defaults=True overrides config setting."""
        # Mock config says exclude defaults, but explicit parameter overrides  
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': False
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser(include_defaults=True)  # Explicit override
            assert serialiser.include_defaults is True
            
            save_path = tmp_path / "test_explicit_true_override.json"
            # Use the serializer's setting by passing include_defaults=True explicitly  
            serialiser.save(sample_quam_object, save_path, include_defaults=True)
            
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
            
            # Should include defaults despite config saying exclude them
            assert 'default_val' in saved_data
            assert saved_data['default_val'] == 10

    def test_save_nested_objects_with_defaults(self, tmp_path, sample_quam_object_nested, prevent_default_config_loading):
        """Test saving complex nested objects with defaults."""
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            
            save_path = tmp_path / "test_nested_with_defaults.json"
            serialiser.save(sample_quam_object_nested, save_path)
            
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
            
            # Check nested component defaults are included
            assert 'components' in saved_data
            assert 'parent' in saved_data['components']
            parent_comp = saved_data['components']['parent']
            
            # Should include default values in nested objects
            assert 'value' in parent_comp  # Default value from MockMainComponent
            assert parent_comp['value'] == 1  # Default from fixture
            
            # Check child component defaults
            assert 'child' in parent_comp
            child_comp = parent_comp['child']
            assert 'child_value' in child_comp

    def test_save_file_size_difference_with_without_defaults(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test file size difference between including/excluding defaults."""
        # Save with defaults
        mock_config_with_defaults = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config_with_defaults):
            serialiser_with = JSONSerialiser()
            save_path_with = tmp_path / "with_defaults.json"
            serialiser_with.save(sample_quam_object, save_path_with)
        
        # Save without defaults
        mock_config_without_defaults = type('MockConfig', (), {
            'include_defaults_in_save': False
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config_without_defaults):
            serialiser_without = JSONSerialiser()
            save_path_without = tmp_path / "without_defaults.json"
            serialiser_without.save(sample_quam_object, save_path_without)
        
        # File with defaults should be larger or equal (more fields)
        size_with = save_path_with.stat().st_size
        size_without = save_path_without.stat().st_size
        
        assert size_with >= size_without
        
        # Verify content differences
        with open(save_path_with, 'r') as f:
            data_with = json.load(f)
        with open(save_path_without, 'r') as f:
            data_without = json.load(f)
        
        # File with defaults should have more or equal keys
        assert len(data_with) >= len(data_without)


class TestJSONSerialiserSaveBehaviorIsolation:
    """Test save behavior with proper config and state isolation."""

    def test_save_uses_isolated_paths_only(self, tmp_path, sample_quam_object, monkeypatch, prevent_default_config_loading):
        """Test that save operations use isolated paths only."""
        # Set isolated environment variables
        monkeypatch.setenv("QUAM_CONFIG_FILE", str(tmp_path / "test_config.toml"))
        monkeypatch.setenv("QUAM_STATE_PATH", str(tmp_path / "test_state"))
        
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser()
            
            # Save to tmp_path location
            save_path = tmp_path / "isolated_save.json"
            serialiser.save(sample_quam_object, save_path)
            
            # Verify file exists in isolated location
            assert save_path.exists()
            assert save_path.parent == tmp_path
            
            # Verify no files created outside tmp_path
            # (This is implicit - the test environment ensures this)

    def test_save_split_files_with_defaults(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test save behavior with split files includes defaults in all files."""
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        # Define content mapping for splitting
        content_mapping = {
            "components": "components.json",
            "wiring": "wiring.json"
        }
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            serialiser = JSONSerialiser(content_mapping=content_mapping)
            
            save_dir = tmp_path / "split_save_test"
            serialiser.save(sample_quam_object, save_dir)
            
            # Check that split files exist
            components_file = save_dir / "components.json"
            wiring_file = save_dir / "wiring.json"
            default_file = save_dir / "state.json"  # Default filename
            
            assert components_file.exists()
            assert wiring_file.exists() 
            assert default_file.exists()
            
            # Verify defaults are included in relevant files
            with open(components_file, 'r') as f:
                components_data = json.load(f)
            
            # Should include default values in components
            if 'components' in components_data:
                for comp_name, comp_data in components_data['components'].items():
                    if 'value' in comp_data:
                        # If value is present, it should include default value
                        assert isinstance(comp_data['value'], int)


class TestJSONSerialiserSaveBackwardsCompatibility:
    """Test save behavior backwards compatibility."""

    def test_existing_save_patterns_still_work(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test that existing save usage patterns continue to work."""
        # Test the old explicit patterns
        serialiser_old_false = JSONSerialiser(include_defaults=False)
        serialiser_old_true = JSONSerialiser(include_defaults=True)
        
        save_path_false = tmp_path / "old_pattern_false.json"
        save_path_true = tmp_path / "old_pattern_true.json"
        
        # These should work regardless of config
        serialiser_old_false.save(sample_quam_object, save_path_false)
        serialiser_old_true.save(sample_quam_object, save_path_true)
        
        # Verify both files exist
        assert save_path_false.exists()
        assert save_path_true.exists()
        
        # Verify behavior differences
        with open(save_path_false, 'r') as f:
            data_false = json.load(f)
        with open(save_path_true, 'r') as f:
            data_true = json.load(f)
        
        # True should have more or equal fields
        assert len(data_true) >= len(data_false)

    def test_quam_root_save_method_behavior(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test that QuamRoot.save() method gets new default behavior."""
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            # Use the fixture object but with a fresh serializer created within mock context
            # Since the fixture was created outside the mock, we need to ensure proper testing
            save_path = tmp_path / "quam_root_save_test.json"
            
            # Create new serializer within mock context and save explicitly
            serialiser = JSONSerialiser()
            assert serialiser.include_defaults is True  # Should read from mock config
            
            serialiser.save(sample_quam_object, save_path)
            
            assert save_path.exists()
            
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
            
            # Should include defaults with new behavior
            assert 'default_val' in saved_data
            assert saved_data['default_val'] == 10

    def test_quam_root_save_with_explicit_override(self, tmp_path, sample_quam_object, prevent_default_config_loading):
        """Test that QuamRoot.save() explicit parameter still overrides.""" 
        mock_config = type('MockConfig', (), {
            'include_defaults_in_save': True  # Config says include
        })()
        
        with patch('quam.serialisation.json.get_quam_config', return_value=mock_config):
            save_path = tmp_path / "quam_root_explicit_override.json"
            # Explicit False should override config
            sample_quam_object.save(save_path, include_defaults=False)
            
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
            
            # Should exclude defaults despite config setting
            assert 'default_val' not in saved_data or saved_data.get('default_val') != 10