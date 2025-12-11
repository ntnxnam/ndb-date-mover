"""
Configuration Loader Module

Loads and validates the fields configuration file for JIRA date tracking.

Author: NDB Date Mover Team
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""

    pass


class ConfigLoader:
    """
    Loads and validates the fields configuration file.
    
    Attributes:
        config_path (Path): Path to the configuration file
        config_data (Dict): Loaded configuration data
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to config file. If not provided, looks for
                        config/fields.json in project root
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to config/fields.json in project root
            project_root = Path(__file__).parent.parent
            self.config_path = project_root / "config" / "fields.json"

        self.config_data: Optional[Dict] = None
        logger.info(f"ConfigLoader initialized with path: {self.config_path}")

    def load(self) -> Dict:
        """
        Load and validate the configuration file.
        
        Returns:
            Dict: Configuration data
            
        Raises:
            ConfigValidationError: If config file is invalid
            FileNotFoundError: If config file doesn't exist
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}. "
                f"Please create config/fields.json based on config/fields.json.example"
            )

        try:
            with open(self.config_path, "r") as f:
                self.config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(
                f"Invalid JSON in configuration file: {str(e)}"
            ) from e

        # Validate configuration structure
        self._validate()

        logger.info("Configuration loaded successfully")
        return self.config_data

    def _validate(self):
        """
        Validate the configuration structure.
        
        Raises:
            ConfigValidationError: If validation fails
        """
        if not self.config_data:
            raise ConfigValidationError("Configuration data is empty")

        # Validate custom_fields
        if "custom_fields" not in self.config_data:
            raise ConfigValidationError(
                "Configuration missing required field: 'custom_fields'"
            )

        if not isinstance(self.config_data["custom_fields"], list):
            raise ConfigValidationError("'custom_fields' must be a list")

        # Validate each custom field
        seen_field_ids = set()
        for idx, field in enumerate(self.config_data["custom_fields"]):
            if not isinstance(field, dict):
                raise ConfigValidationError(
                    f"custom_fields[{idx}] must be a dictionary"
                )

            if "id" not in field:
                raise ConfigValidationError(
                    f"custom_fields[{idx}] missing required field: 'id'"
                )

            field_id = field["id"]
            if field_id in seen_field_ids:
                raise ConfigValidationError(
                    f"Duplicate field ID found: {field_id}"
                )
            seen_field_ids.add(field_id)

            # Validate field ID format (should start with customfield_)
            if not field_id.startswith("customfield_") and field_id not in [
                "key",
                "summary",
                "status",
                "assignee",
                "created",
                "updated",
            ]:
                logger.warning(
                    f"Field ID '{field_id}' doesn't follow standard format"
                )

            # Validate type if provided
            if "type" in field and field["type"] not in ["date", "string", "number"]:
                logger.warning(
                    f"Unknown field type '{field['type']}' for field {field_id}"
                )

        # Validate display_columns
        if "display_columns" not in self.config_data:
            raise ConfigValidationError(
                "Configuration missing required field: 'display_columns'"
            )

        if not isinstance(self.config_data["display_columns"], list):
            raise ConfigValidationError("'display_columns' must be a list")

        if len(self.config_data["display_columns"]) == 0:
            raise ConfigValidationError("'display_columns' cannot be empty")

        # Validate date_format if provided
        if "date_format" in self.config_data:
            date_format = self.config_data["date_format"]
            if date_format not in ["mm/dd/yyyy", "yyyy-mm-dd", "dd/mm/yyyy"]:
                logger.warning(f"Unsupported date format: {date_format}")

        logger.debug("Configuration validation passed")

    def get_custom_fields(self) -> List[Dict]:
        """
        Get the list of custom fields from configuration.
        
        Returns:
            List[Dict]: List of custom field configurations
        """
        if not self.config_data:
            self.load()
        return self.config_data.get("custom_fields", [])

    def get_display_columns(self) -> List[str]:
        """
        Get the list of columns to display.
        
        Returns:
            List[str]: List of column IDs
        """
        if not self.config_data:
            self.load()
        return self.config_data.get("display_columns", [])

    def get_date_fields(self) -> List[Dict]:
        """
        Get date fields that should track history.
        
        Returns:
            List[Dict]: List of date field configurations with track_history=True
        """
        if not self.config_data:
            self.load()
        return [
            field
            for field in self.config_data.get("custom_fields", [])
            if field.get("type") == "date" and field.get("track_history", False)
        ]

    def get_date_format(self) -> str:
        """
        Get the date format from configuration.
        
        Returns:
            str: Date format string (default: mm/dd/yyyy)
        """
        if not self.config_data:
            self.load()
        return self.config_data.get("date_format", "mm/dd/yyyy")


def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Dict: Configuration data
    """
    loader = ConfigLoader(config_path)
    return loader.load()

