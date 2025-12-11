"""
Unit tests for JIRA Client Changelog functionality

Tests for changelog retrieval with proper JIRA API v2 format handling.

Author: NDB Date Mover Team
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.jira_client import JiraClient


class TestJiraClientChangelog:
    """Test cases for changelog retrieval."""
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_issue_changelog_expand_format(self):
        """Test changelog retrieval using expand=changelog format."""
        client = JiraClient("https://test.atlassian.net", "test_token")
        
        # Mock response with expand=changelog format
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            "key": "TEST-123",
            "changelog": {
                "histories": [
                    {
                        "created": "2024-12-25T10:00:00.000+0000",
                        "items": [
                            {
                                "fieldId": "11067",  # Numeric format
                                "field": "Code Complete Date",
                                "fromString": "2024-11-15",
                                "toString": "2024-12-25"
                            }
                        ]
                    }
                ]
            }
        }
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            changes = client.get_issue_changelog("TEST-123")
            
            assert len(changes) == 1
            assert changes[0]["field"] == "customfield_11067"  # Normalized
            assert changes[0]["field_original"] == "11067"  # Original
            assert changes[0]["to"] == "2024-12-25"
            assert changes[0]["from"] == "2024-11-15"
            assert changes[0]["timestamp"] == "2024-12-25T10:00:00.000+0000"
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_issue_changelog_with_field_filter(self):
        """Test changelog retrieval with field ID filter."""
        client = JiraClient("https://test.atlassian.net", "test_token")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            "key": "TEST-123",
            "changelog": {
                "histories": [
                    {
                        "created": "2024-12-25T10:00:00.000+0000",
                        "items": [
                            {
                                "fieldId": "11067",
                                "field": "Code Complete Date",
                                "fromString": "2024-11-15",
                                "toString": "2024-12-25"
                            },
                            {
                                "fieldId": "status",
                                "field": "Status",
                                "fromString": "Open",
                                "toString": "In Progress"
                            }
                        ]
                    }
                ]
            }
        }
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            # Filter by custom field
            changes = client.get_issue_changelog("TEST-123", field_id="customfield_11067")
            
            assert len(changes) == 1
            assert changes[0]["field"] == "customfield_11067"
            assert changes[0]["to"] == "2024-12-25"
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_issue_changelog_numeric_field_id(self):
        """Test changelog with numeric field ID (should be normalized)."""
        client = JiraClient("https://test.atlassian.net", "test_token")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            "key": "TEST-123",
            "changelog": {
                "histories": [
                    {
                        "created": "2024-12-25T10:00:00.000+0000",
                        "items": [
                            {
                                "fieldId": 11067,  # Integer format
                                "field": "Code Complete Date",
                                "fromString": "2024-11-15",
                                "toString": "2024-12-25"
                            }
                        ]
                    }
                ]
            }
        }
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            changes = client.get_issue_changelog("TEST-123")
            
            assert len(changes) == 1
            assert changes[0]["field"] == "customfield_11067"  # Normalized from integer
            assert changes[0]["field_original"] == 11067
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_issue_changelog_standard_field(self):
        """Test changelog with standard field (should not be normalized)."""
        client = JiraClient("https://test.atlassian.net", "test_token")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            "key": "TEST-123",
            "changelog": {
                "histories": [
                    {
                        "created": "2024-12-25T10:00:00.000+0000",
                        "items": [
                            {
                                "fieldId": "status",
                                "field": "Status",
                                "fromString": "Open",
                                "toString": "In Progress"
                            }
                        ]
                    }
                ]
            }
        }
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            changes = client.get_issue_changelog("TEST-123")
            
            assert len(changes) == 1
            assert changes[0]["field"] == "status"  # Not normalized (standard field)
            assert changes[0]["to"] == "In Progress"
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_normalize_field_id_numeric(self):
        """Test field ID normalization for numeric IDs."""
        client = JiraClient("https://test.atlassian.net", "test_token")
        
        # Test numeric string
        assert client._normalize_field_id("11067") == "customfield_11067"
        assert client._normalize_field_id("35863") == "customfield_35863"
        
        # Test integer
        assert client._normalize_field_id(11067) == "customfield_11067"
        
        # Test already normalized
        assert client._normalize_field_id("customfield_11067") == "customfield_11067"
        
        # Test standard fields (should not be normalized)
        assert client._normalize_field_id("key") == "key"
        assert client._normalize_field_id("status") == "status"
        assert client._normalize_field_id("summary") == "summary"
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_issue_changelog_404(self):
        """Test handling when issue is not found."""
        client = JiraClient("https://test.atlassian.net", "test_token")
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {'content-type': 'application/json'}
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            changes = client.get_issue_changelog("TEST-999")
            
            assert changes == []
    
    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_issue_changelog_empty_histories(self):
        """Test handling when changelog has no histories."""
        client = JiraClient("https://test.atlassian.net", "test_token")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            "key": "TEST-123",
            "changelog": {
                "histories": []
            }
        }
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            changes = client.get_issue_changelog("TEST-123")
            
            assert changes == []

