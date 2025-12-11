"""
Unit tests for JIRA Client Filter ID Handling

Tests for handling filter IDs in JQL queries.

Note on Environment Variables:
- Tests use @patch.dict('os.environ', ...) to mock environment variables
- This is intentional: unit tests should be isolated and not depend on .env files
- The JiraClient uses load_dotenv() which loads .env into os.environ
- Patching os.environ simulates environment variables without requiring .env file
- This ensures tests are reproducible and don't require actual JIRA credentials

Author: NDB Date Mover Team
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, patch
from backend.jira_client import JiraClient


class TestJiraClientFilterHandling:
    """Test cases for filter ID handling in JIRA client."""

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_filter_id_conversion(self):
        """
        Test that filter=12345 is converted to filter = 12345.
        
        Note: Uses @patch.dict to mock environment variables instead of .env file
        to ensure test isolation and reproducibility.
        """
        """Test that filter=12345 is converted to filter = 12345."""
        client = JiraClient()
        
        # Mock successful response
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
            result = client.execute_jql("filter=165194")
            
            # Verify the filter was converted
            call_args = client._make_request_with_retry.call_args
            params = call_args[1].get('params', {})
            assert "filter = 165194" in params.get('jql', '')
            assert result["success"] is True

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_filter_id_invalid_format(self):
        """
        Test that invalid filter ID format returns error.
        
        Note: Uses @patch.dict to mock environment variables instead of .env file.
        """
        client = JiraClient()
        
        result = client.execute_jql("filter=abc123")
        
        assert result["success"] is False
        assert "Invalid filter ID format" in result["error"]
        assert "numeric" in result["error"]

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_filter_id_html_response(self):
        """
        Test handling of HTML response when filter doesn't exist or auth fails.
        
        Note: Uses @patch.dict to mock environment variables instead of .env file.
        """
        client = JiraClient()
        
        # Mock HTML response (like login page)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        mock_response.text = '<!DOCTYPE html><html><body>Login</body></html>'
        mock_response.json.side_effect = ValueError("Expecting value")
        
        with patch.object(client, '_make_request_with_retry', return_value=mock_response):
            result = client.execute_jql("filter=165194")
            
            assert result["success"] is False
            assert "HTML page instead of JSON" in result["error"]
            assert "Authentication" in result["error"] or "credentials" in result["error"]

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_filter_id_with_whitespace(self):
        """
        Test filter ID with whitespace is handled correctly.
        
        Note: Uses @patch.dict to mock environment variables instead of .env file.
        """
        client = JiraClient()
        
        # Mock successful response
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
            result = client.execute_jql("filter= 165194 ")
            
            # Should strip whitespace and work
            call_args = client._make_request_with_retry.call_args
            params = call_args[1].get('params', {})
            assert "filter = 165194" in params.get('jql', '')

    @patch.dict('os.environ', {
        'JIRA_URL': 'https://test.atlassian.net',
        'JIRA_PAT_TOKEN': 'test_token'
    })
    def test_regular_jql_not_affected(self):
        """
        Test that regular JQL queries are not affected by filter handling.
        
        Note: Uses @patch.dict to mock environment variables instead of .env file.
        """
        client = JiraClient()
        
        # Mock successful response
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
            result = client.execute_jql("project = TEST AND status = 'In Progress'")
            
            # Should not modify regular JQL
            call_args = client._make_request_with_retry.call_args
            params = call_args[1].get('params', {})
            assert params.get('jql') == "project = TEST AND status = 'In Progress'"
            assert result["success"] is True

