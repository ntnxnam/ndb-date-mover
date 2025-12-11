"""
Unit tests for JIRA Client JSON Parsing Error Handling

Tests for handling non-JSON responses from JIRA API.

Author: NDB Date Mover Team
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.jira_client import JiraClient


class TestJiraClientJSONParsing:
    """Test cases for JSON parsing error handling in JIRA client."""

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_execute_jql_non_json_response(self):
        """Test JQL execution with non-JSON response (HTML error page)."""
        client = JiraClient()
        
        # Mock response with HTML content instead of JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        mock_response.text = '<html><body>Error 500: Internal Server Error</body></html>'
        mock_response.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            result = client.execute_jql("project = TEST")
            
            assert result["success"] is False
            assert "invalid response format" in result["error"].lower()
            assert "JIRA URL" in result["error"] or "connection" in result["error"]
            assert result["issues"] == []
            assert result["total"] == 0

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_execute_jql_missing_content_type(self):
        """Test JQL execution with missing content-type header."""
        client = JiraClient()
        
        # Mock response without content-type
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = 'Invalid response'
        mock_response.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            result = client.execute_jql("project = TEST")
            
            assert result["success"] is False
            assert "invalid response format" in result["error"].lower()

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_execute_jql_valid_json_response(self):
        """Test JQL execution with valid JSON response."""
        client = JiraClient()
        
        # Mock valid JSON response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'issues': [],
            'total': 0,
            'startAt': 0,
            'maxResults': 100
        }
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            result = client.execute_jql("project = TEST")
            
            assert result["success"] is True
            assert result["issues"] == []
            assert result["total"] == 0

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_field_metadata_non_json_response(self):
        """Test field metadata retrieval with non-JSON response."""
        client = JiraClient()
        
        # Mock HTML response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.json.side_effect = ValueError("Expecting value")
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            result = client.get_field_metadata()
            
            # Should return empty dict on error, not crash
            assert isinstance(result, dict)
            assert result == {}

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_get_issue_changelog_non_json_response(self):
        """Test changelog retrieval with non-JSON response."""
        client = JiraClient()
        
        # Mock HTML response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.json.side_effect = ValueError("Expecting value")
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            result = client.get_issue_changelog("TEST-123")
            
            # Should return empty list on error, not crash
            assert isinstance(result, list)
            assert result == []

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_error_response_with_text_content(self):
        """Test error response that contains text instead of JSON."""
        client = JiraClient()
        
        # Mock 400 error with text content
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {'content-type': 'text/plain'}
        mock_response.text = 'Bad Request: Invalid query syntax'
        mock_response.json.side_effect = ValueError("Expecting value")
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            result = client.execute_jql("invalid query")
            
            assert result["success"] is False
            assert "Invalid JQL query" in result["error"] or "Bad Request" in result["error"]
            # Should use text response when JSON parsing fails
            assert result["error"] is not None

