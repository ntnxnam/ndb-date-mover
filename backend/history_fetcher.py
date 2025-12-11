"""
History Fetcher Module

Fetches historical date changes from JIRA for configured date fields and specific issue keys.
Only fetches history for date fields that are configured in config/fields.json with track_history=true.

Author: NDB Date Mover Team
"""

import logging
from typing import Dict, List, Optional

from backend.jira_client import JiraClient
from backend.config_loader import ConfigLoader
from backend.date_utils import (
    format_date,
    calculate_week_slip,
    extract_date_history,
    get_week_slip_color,
)

logger = logging.getLogger(__name__)


class HistoryFetcher:
    """
    Fetches historical date changes from JIRA for configured date fields.
    
    Only fetches history for:
    - Date fields specified in config/fields.json
    - Fields with track_history=true
    - Specific JIRA issue keys provided
    """
    
    def __init__(self, jira_client: JiraClient, config_loader: Optional[ConfigLoader] = None):
        """
        Initialize the history fetcher.
        
        Args:
            jira_client: JIRA client instance for API calls
            config_loader: Optional config loader. If not provided, creates a new one.
        """
        self.client = jira_client
        self.config_loader = config_loader or ConfigLoader()
        self._config = None
        self._date_fields = None
        self._date_format = None
        
    def _load_config(self):
        """Load configuration if not already loaded."""
        if self._config is None:
            try:
                self._config = self.config_loader.load()
                self._date_fields = self.config_loader.get_date_fields()
                self._date_format = self.config_loader.get_date_format()
                logger.debug(f"Loaded config with {len(self._date_fields)} date fields to track")
            except Exception as e:
                logger.warning(f"Could not load configuration: {str(e)}")
                self._date_fields = []
                self._date_format = "mm/dd/yyyy"  # Default display format
    
    def fetch_history_for_issues(
        self, 
        issue_keys: List[str], 
        include_history: bool = True
    ) -> Dict[str, Dict]:
        """
        Fetch historical date changes for multiple JIRA issues.
        
        Only fetches history for date fields configured in config/fields.json
        with track_history=true.
        
        Args:
            issue_keys: List of JIRA issue keys (e.g., ["PROJ-123", "PROJ-456"])
            include_history: Whether to fetch and include historical dates
            
        Returns:
            Dict[str, Dict]: Dictionary keyed by issue key, containing:
                {
                    "PROJ-123": {
                        "customfield_11067": {
                            "current": "12/25/2024",
                            "current_raw": "2024-12-25T00:00:00.000+0000",
                            "history": ["11/15/2024", "10/01/2024"],
                            "history_raw": ["2024-11-15T00:00:00.000+0000", "2024-10-01T00:00:00.000+0000"],
                            "week_slip": {
                                "weeks": 3,
                                "display": "+3 weeks",
                                "color": "red"
                            }
                        },
                        ...
                    },
                    ...
                }
        """
        self._load_config()
        
        if not issue_keys:
            logger.warning("No issue keys provided for history fetching")
            return {}
        
        if not self._date_fields:
            logger.warning("No date fields configured for history tracking")
            return {issue_key: {} for issue_key in issue_keys}
        
        results = {}
        
        for issue_key in issue_keys:
            try:
                issue_history = self.fetch_history_for_issue(issue_key, include_history)
                results[issue_key] = issue_history
            except Exception as e:
                logger.error(f"Error fetching history for {issue_key}: {str(e)}")
                results[issue_key] = {}
        
        logger.info(f"Fetched history for {len(results)} issues")
        return results
    
    def fetch_history_for_issue(
        self, 
        issue_key: str, 
        include_history: bool = True
    ) -> Dict[str, Dict]:
        """
        Fetch historical date changes for a single JIRA issue.
        
        Only fetches history for date fields configured in config/fields.json
        with track_history=true.
        
        Args:
            issue_key: JIRA issue key (e.g., "PROJ-123")
            include_history: Whether to fetch and include historical dates
            
        Returns:
            Dict[str, Dict]: Dictionary keyed by field ID, containing:
                {
                    "customfield_11067": {
                        "current": "12/25/2024",
                        "current_raw": "2024-12-25T00:00:00.000+0000",
                        "history": ["11/15/2024", "10/01/2024"],
                        "history_raw": ["2024-11-15T00:00:00.000+0000", "2024-10-01T00:00:00.000+0000"],
                        "week_slip": {
                            "weeks": 3,
                            "display": "+3 weeks",
                            "color": "red"
                        }
                    },
                    ...
                }
        """
        self._load_config()
        
        if not self._date_fields:
            logger.warning(f"No date fields configured for history tracking")
            return {}
        
        logger.info(f"Fetching history for issue {issue_key}")
        
        # First, get the current issue to get current date values
        try:
            # Execute a simple query to get the issue
            query_result = self.client.execute_jql(f"key = {issue_key}", max_results=1)
            
            if not query_result.get("success") or not query_result.get("issues"):
                logger.warning(f"Issue {issue_key} not found or not accessible")
                return {}
            
            issue = query_result["issues"][0]
            fields = issue.get("fields", {})
        except Exception as e:
            logger.error(f"Error fetching issue {issue_key}: {str(e)}")
            return {}
        
        result = {}
        
        # Process each configured date field
        for date_field_config in self._date_fields:
            field_id = date_field_config.get("id")
            
            if not field_id:
                continue
            
            # Get current value
            current_value = fields.get(field_id)
            
            if not current_value:
                logger.debug(f"No current value for {issue_key}/{field_id}")
                continue
            
            # Format current date for display
            formatted_current = format_date(str(current_value), self._date_format)
            
            field_result = {
                "current": formatted_current,
                "current_raw": str(current_value),
            }
            
            # Fetch history if requested and field is configured to track history
            if include_history and date_field_config.get("track_history"):
                try:
                    # Fetch changelog for this specific field
                    changelog = self.client.get_issue_changelog(issue_key, field_id)
                    date_history = extract_date_history(changelog, field_id)
                    
                    # Format historical dates
                    formatted_history = []
                    raw_history = []
                    
                    for date_val, timestamp in date_history:
                        # Only include dates that are different from current
                        if date_val != current_value:
                            formatted_history.append(format_date(date_val, self._date_format))
                            raw_history.append(date_val)
                    
                    field_result["history"] = formatted_history
                    field_result["history_raw"] = raw_history
                    
                    # Calculate week slip
                    if date_history:
                        original_date = date_history[0][0]  # First date in history
                        weeks, week_str = calculate_week_slip(original_date, str(current_value))
                        field_result["week_slip"] = {
                            "weeks": weeks,
                            "display": week_str,
                            "color": get_week_slip_color(weeks),
                        }
                    else:
                        field_result["week_slip"] = {
                            "weeks": 0,
                            "display": "0 weeks",
                            "color": "gray",
                        }
                    
                    logger.debug(
                        f"Fetched {len(formatted_history)} historical dates for {issue_key}/{field_id}"
                    )
                    
                except Exception as e:
                    logger.warning(
                        f"Error fetching history for {issue_key}/{field_id}: {str(e)}"
                    )
                    field_result["history"] = []
                    field_result["history_raw"] = []
                    field_result["week_slip"] = {
                        "weeks": 0,
                        "display": "N/A",
                        "color": "gray",
                    }
            else:
                # No history requested or field not configured to track history
                field_result["history"] = []
                field_result["history_raw"] = []
                field_result["week_slip"] = None
            
            result[field_id] = field_result
        
        logger.info(f"Fetched history for {issue_key}: {len(result)} date fields")
        return result
    
    def get_configured_date_fields(self) -> List[Dict]:
        """
        Get the list of date fields configured for history tracking.
        
        Returns:
            List[Dict]: List of date field configurations with track_history=True
        """
        self._load_config()
        return self._date_fields or []

