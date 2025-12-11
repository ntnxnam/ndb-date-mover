"""
Unit tests for History Fetcher Module

Tests for fetching historical date changes from JIRA for configured date fields.

Author: NDB Date Mover Team
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.history_fetcher import HistoryFetcher
from backend.jira_client import JiraClient
from backend.config_loader import ConfigLoader


class TestHistoryFetcherInitialization:
    """Test cases for HistoryFetcher initialization."""
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_init_with_client_and_config(self):
        """Test initialization with JIRA client and config loader."""
        mock_client = Mock(spec=JiraClient)
        mock_config = Mock(spec=ConfigLoader)
        
        fetcher = HistoryFetcher(mock_client, mock_config)
        
        assert fetcher.client == mock_client
        assert fetcher.config_loader == mock_config
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_init_with_client_only(self):
        """Test initialization with only JIRA client (creates config loader)."""
        mock_client = Mock(spec=JiraClient)
        
        fetcher = HistoryFetcher(mock_client)
        
        assert fetcher.client == mock_client
        assert isinstance(fetcher.config_loader, ConfigLoader)


class TestHistoryFetcherConfig:
    """Test cases for configuration loading."""
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_load_config_success(self):
        """Test successful configuration loading."""
        mock_client = Mock(spec=JiraClient)
        mock_config = Mock(spec=ConfigLoader)
        
        mock_config.load.return_value = {
            "custom_fields": [
                {
                    "id": "customfield_11067",
                    "type": "date",
                    "track_history": True
                }
            ]
        }
        mock_config.get_date_fields.return_value = [
            {"id": "customfield_11067", "type": "date", "track_history": True}
        ]
        mock_config.get_date_format.return_value = "mm/dd/yyyy"
        
        fetcher = HistoryFetcher(mock_client, mock_config)
        fetcher._load_config()
        
        assert fetcher._config is not None
        assert len(fetcher._date_fields) == 1
        assert fetcher._date_format == "mm/dd/yyyy"
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_load_config_failure(self):
        """Test configuration loading failure (uses defaults)."""
        mock_client = Mock(spec=JiraClient)
        mock_config = Mock(spec=ConfigLoader)
        
        mock_config.load.side_effect = Exception("Config error")
        
        fetcher = HistoryFetcher(mock_client, mock_config)
        fetcher._load_config()
        
        assert fetcher._date_fields == []
        assert fetcher._date_format == "mm/dd/yyyy"


class TestHistoryFetcherSingleIssue:
    """Test cases for fetching history for a single issue."""
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_fetch_history_for_issue_success(self):
        """Test successful history fetch for a single issue."""
        mock_client = Mock(spec=JiraClient)
        mock_config = Mock(spec=ConfigLoader)
        
        # Setup config
        mock_config.load.return_value = {
            "custom_fields": [
                {
                    "id": "customfield_11067",
                    "type": "date",
                    "track_history": True
                }
            ]
        }
        mock_config.get_date_fields.return_value = [
            {"id": "customfield_11067", "type": "date", "track_history": True}
        ]
        mock_config.get_date_format.return_value = "mm/dd/yyyy"
        
        # Setup JIRA client responses
        mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [{
                "key": "TEST-123",
                "fields": {
                    "customfield_11067": "2024-12-25T00:00:00.000+0000"
                }
            }]
        }
        
        mock_client.get_issue_changelog.return_value = [
            {
                "field": "customfield_11067",
                "from": "2024-10-01T00:00:00.000+0000",
                "to": "2024-11-15T00:00:00.000+0000",
                "timestamp": "2024-11-15T10:00:00.000+0000"
            },
            {
                "field": "customfield_11067",
                "from": "2024-11-15T00:00:00.000+0000",
                "to": "2024-12-25T00:00:00.000+0000",
                "timestamp": "2024-12-25T10:00:00.000+0000"
            }
        ]
        
        fetcher = HistoryFetcher(mock_client, mock_config)
        result = fetcher.fetch_history_for_issue("TEST-123", include_history=True)
        
        assert "customfield_11067" in result
        assert result["customfield_11067"]["current"] == "12/25/2024"
        assert len(result["customfield_11067"]["history"]) > 0
        assert result["customfield_11067"]["week_slip"] is not None
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_fetch_history_for_issue_not_found(self):
        """Test handling when issue is not found."""
        mock_client = Mock(spec=JiraClient)
        mock_config = Mock(spec=ConfigLoader)
        
        mock_config.load.return_value = {"custom_fields": []}
        mock_config.get_date_fields.return_value = []
        mock_config.get_date_format.return_value = "mm/dd/yyyy"
        
        mock_client.execute_jql.return_value = {
            "success": False,
            "issues": []
        }
        
        fetcher = HistoryFetcher(mock_client, mock_config)
        result = fetcher.fetch_history_for_issue("TEST-999", include_history=True)
        
        assert result == {}


class TestHistoryFetcherMultipleIssues:
    """Test cases for fetching history for multiple issues."""
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_fetch_history_for_issues_success(self):
        """Test successful history fetch for multiple issues."""
        mock_client = Mock(spec=JiraClient)
        mock_config = Mock(spec=ConfigLoader)
        
        # Setup config
        mock_config.load.return_value = {
            "custom_fields": [
                {
                    "id": "customfield_11067",
                    "type": "date",
                    "track_history": True
                }
            ]
        }
        mock_config.get_date_fields.return_value = [
            {"id": "customfield_11067", "type": "date", "track_history": True}
        ]
        mock_config.get_date_format.return_value = "mm/dd/yyyy"
        
        # Setup JIRA client to return different issues
        def mock_execute_jql(jql, **kwargs):
            if "TEST-123" in jql:
                return {
                    "success": True,
                    "issues": [{
                        "key": "TEST-123",
                        "fields": {
                            "customfield_11067": "2024-12-25T00:00:00.000+0000"
                        }
                    }]
                }
            elif "TEST-456" in jql:
                return {
                    "success": True,
                    "issues": [{
                        "key": "TEST-456",
                        "fields": {
                            "customfield_11067": "2024-12-20T00:00:00.000+0000"
                        }
                    }]
                }
            return {"success": False, "issues": []}
        
        mock_client.execute_jql.side_effect = mock_execute_jql
        mock_client.get_issue_changelog.return_value = []
        
        fetcher = HistoryFetcher(mock_client, mock_config)
        result = fetcher.fetch_history_for_issues(["TEST-123", "TEST-456"], include_history=True)
        
        assert "TEST-123" in result
        assert "TEST-456" in result
        assert len(result) == 2
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_fetch_history_for_issues_empty_list(self):
        """Test handling when no issue keys provided."""
        mock_client = Mock(spec=JiraClient)
        mock_config = Mock(spec=ConfigLoader)
        
        fetcher = HistoryFetcher(mock_client, mock_config)
        result = fetcher.fetch_history_for_issues([], include_history=True)
        
        assert result == {}


class TestHistoryFetcherConfiguredFields:
    """Test cases for getting configured date fields."""
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_configured_date_fields(self):
        """Test getting list of configured date fields."""
        mock_client = Mock(spec=JiraClient)
        mock_config = Mock(spec=ConfigLoader)
        
        date_fields = [
            {"id": "customfield_11067", "type": "date", "track_history": True},
            {"id": "customfield_35863", "type": "date", "track_history": True}
        ]
        
        mock_config.load.return_value = {"custom_fields": date_fields}
        mock_config.get_date_fields.return_value = date_fields
        mock_config.get_date_format.return_value = "mm/dd/yyyy"
        
        fetcher = HistoryFetcher(mock_client, mock_config)
        fields = fetcher.get_configured_date_fields()
        
        assert len(fields) == 2
        assert fields[0]["id"] == "customfield_11067"
        assert fields[1]["id"] == "customfield_35863"

