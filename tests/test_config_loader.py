"""
Unit tests for Configuration Loader

Author: NDB Date Mover Team
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pytest
import tempfile
from unittest.mock import patch

from backend.config_loader import ConfigLoader, ConfigValidationError


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "custom_fields": [
                    {
                        "id": "customfield_12345",
                        "type": "date",
                        "track_history": True
                    }
                ],
                "display_columns": ["key", "summary", "customfield_12345"],
                "date_format": "mm/dd/yyyy"
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            loader = ConfigLoader(config_path)
            config = loader.load()
            assert config == config_data
            assert loader.get_custom_fields() == config_data["custom_fields"]
            assert loader.get_display_columns() == config_data["display_columns"]
        finally:
            Path(config_path).unlink()

    def test_load_missing_file(self):
        """Test loading a non-existent configuration file."""
        loader = ConfigLoader("/nonexistent/path/config.json")
        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {")
            config_path = f.name

        try:
            loader = ConfigLoader(config_path)
            with pytest.raises(ConfigValidationError):
                loader.load()
        finally:
            Path(config_path).unlink()

    def test_validate_missing_custom_fields(self):
        """Test validation with missing custom_fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"display_columns": ["key"]}, f)
            config_path = f.name

        try:
            loader = ConfigLoader(config_path)
            with pytest.raises(ConfigValidationError, match="custom_fields"):
                loader.load()
        finally:
            Path(config_path).unlink()

    def test_validate_duplicate_field_ids(self):
        """Test validation with duplicate field IDs."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "custom_fields": [
                    {"id": "customfield_12345", "type": "date"},
                    {"id": "customfield_12345", "type": "date"}
                ],
                "display_columns": ["key"]
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            loader = ConfigLoader(config_path)
            with pytest.raises(ConfigValidationError, match="Duplicate"):
                loader.load()
        finally:
            Path(config_path).unlink()

    def test_get_date_fields(self):
        """Test getting date fields that track history."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "custom_fields": [
                    {"id": "customfield_12345", "type": "date", "track_history": True},
                    {"id": "customfield_67890", "type": "date", "track_history": False},
                    {"id": "customfield_11111", "type": "string", "track_history": True}
                ],
                "display_columns": ["key"]
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            loader = ConfigLoader(config_path)
            loader.load()
            date_fields = loader.get_date_fields()
            assert len(date_fields) == 1
            assert date_fields[0]["id"] == "customfield_12345"
        finally:
            Path(config_path).unlink()
    
    def test_get_display_columns_with_fixversions(self):
        """Test that fixVersions can be included in display columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "custom_fields": [
                    {"id": "customfield_12345", "type": "date", "track_history": True}
                ],
                "display_columns": ["key", "summary", "fixVersions", "customfield_12345"],
                "date_format": "mm/dd/yyyy"
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            loader = ConfigLoader(config_path)
            loader.load()
            columns = loader.get_display_columns()
            assert "fixVersions" in columns
        finally:
            Path(config_path).unlink()
    
    def test_custom_fields_with_ai_summarize(self):
        """Test that custom fields with AI summarization flag are recognized."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "custom_fields": [
                    {
                        "id": "customfield_23073",
                        "type": "text",
                        "track_history": False,
                        "display_name": "Status Update",
                        "ai_summarize": True,
                        "exec_friendly": True
                    }
                ],
                "display_columns": ["key", "customfield_23073"],
                "date_format": "mm/dd/yyyy"
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            loader = ConfigLoader(config_path)
            config = loader.load()
            custom_fields = config.get("custom_fields", [])
            
            # Find Status Update field
            status_field = next(
                (f for f in custom_fields if f.get("id") == "customfield_23073"),
                None
            )
            
            assert status_field is not None
            assert status_field.get("ai_summarize") is True
            assert status_field.get("exec_friendly") is True
        finally:
            Path(config_path).unlink()

