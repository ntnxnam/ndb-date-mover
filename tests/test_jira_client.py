"""
Unit tests for JIRA Client Module

This test suite covers:
- JiraClient initialization
- Connection testing with various scenarios
- Error handling
- User information retrieval

Author: NDB Date Mover Team
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError, RequestException

from jira_client import JiraClient, JiraConnectionError, create_jira_client


class TestJiraClientInitialization:
    """Test cases for JiraClient initialization."""

    def test_init_with_parameters(self):
        """Test initialization with explicit parameters."""
        client = JiraClient(
            base_url="https://test.atlassian.net", pat_token="test_token_123"
        )
        assert client.base_url == "https://test.atlassian.net"
        assert client.pat_token == "test_token_123"
        assert "Authorization" in client.session.headers
        assert "Bearer test_token_123" in client.session.headers["Authorization"]

    def test_init_with_env_variables(self):
        """Test initialization using environment variables."""
        with patch.dict(
            os.environ,
            {
                "JIRA_URL": "https://env-test.atlassian.net",
                "JIRA_PAT_TOKEN": "env_token_456",
            },
        ):
            client = JiraClient()
            assert client.base_url == "https://env-test.atlassian.net"
            assert client.pat_token == "env_token_456"

    def test_init_missing_base_url(self):
        """Test that ValueError is raised when base_url is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="JIRA_URL must be provided"):
                JiraClient()

    def test_init_missing_pat_token(self):
        """Test that ValueError is raised when pat_token is missing."""
        with patch.dict(os.environ, {"JIRA_URL": "https://test.atlassian.net"}, clear=True):
            with pytest.raises(ValueError, match="JIRA_PAT_TOKEN must be provided"):
                JiraClient()

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from base_url."""
        client = JiraClient(
            base_url="https://test.atlassian.net/", pat_token="test_token"
        )
        assert client.base_url == "https://test.atlassian.net"

    def test_init_invalid_url(self):
        """Test that ValueError is raised for invalid URL format."""
        with pytest.raises(ValueError, match="Invalid JIRA URL format"):
            JiraClient(base_url="not-a-valid-url", pat_token="test_token")


class TestJiraClientConnection:
    """Test cases for connection testing."""

    @pytest.fixture
    def client(self):
        """Create a JiraClient instance for testing."""
        return JiraClient(
            base_url="https://test.atlassian.net", pat_token="test_token_123"
        )

    @patch("jira_client.requests.Session.get")
    def test_connection_success(self, mock_get, client):
        """Test successful connection to JIRA."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "serverTitle": "Test JIRA",
            "version": "9.0.0",
            "deploymentType": "Cloud",
        }
        mock_get.return_value = mock_response

        success, result = client.test_connection()

        assert success is True
        assert result["success"] is True
        assert result["message"] == "Connection successful"
        assert result["server_title"] == "Test JIRA"
        assert result["version"] == "9.0.0"
        assert result["deployment_type"] == "Cloud"
        mock_get.assert_called_once()

    @patch("jira_client.requests.Session.get")
    def test_connection_authentication_failure(self, mock_get, client):
        """Test connection failure due to authentication error (401)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        success, result = client.test_connection()

        assert success is False
        assert result["success"] is False
        assert "Authentication failed" in result["message"]
        assert result["status_code"] == 401

    @patch("jira_client.requests.Session.get")
    def test_connection_authorization_failure(self, mock_get, client):
        """Test connection failure due to authorization error (403)."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        success, result = client.test_connection()

        assert success is False
        assert result["success"] is False
        assert "Authorization failed" in result["message"]
        assert result["status_code"] == 403

    @patch("jira_client.requests.Session.get")
    def test_connection_other_error_status(self, mock_get, client):
        """Test connection failure with other error status codes."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_get.return_value = mock_response

        success, result = client.test_connection()

        assert success is False
        assert result["success"] is False
        assert "Connection failed" in result["message"]
        assert result["status_code"] == 500

    @patch("jira_client.requests.Session.get")
    def test_connection_timeout(self, mock_get, client):
        """Test connection timeout handling."""
        mock_get.side_effect = Timeout("Connection timeout")

        success, result = client.test_connection()

        assert success is False
        assert result["success"] is False
        assert "timeout" in result["message"].lower()

    @patch("jira_client.requests.Session.get")
    def test_connection_error(self, mock_get, client):
        """Test connection error handling."""
        mock_get.side_effect = ConnectionError("Unable to connect")

        success, result = client.test_connection()

        assert success is False
        assert result["success"] is False
        assert "Connection error" in result["message"]

    @patch("jira_client.requests.Session.get")
    def test_connection_request_exception(self, mock_get, client):
        """Test general request exception handling."""
        mock_get.side_effect = RequestException("Request failed")

        success, result = client.test_connection()

        assert success is False
        assert result["success"] is False
        assert "Request failed" in result["message"]

    @patch("jira_client.requests.Session.get")
    def test_connection_unexpected_exception(self, mock_get, client):
        """Test handling of unexpected exceptions."""
        mock_get.side_effect = Exception("Unexpected error")

        success, result = client.test_connection()

        assert success is False
        assert result["success"] is False
        assert "Unexpected error" in result["message"]

    @patch("jira_client.requests.Session.get")
    def test_connection_non_json_error_response(self, mock_get, client):
        """Test handling of non-JSON error responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "HTML error page"
        mock_get.return_value = mock_response

        success, result = client.test_connection()

        assert success is False
        assert result["success"] is False
        assert "Connection failed" in result["message"]


class TestJiraClientUserInfo:
    """Test cases for user information retrieval."""

    @pytest.fixture
    def client(self):
        """Create a JiraClient instance for testing."""
        return JiraClient(
            base_url="https://test.atlassian.net", pat_token="test_token_123"
        )

    @patch("jira_client.requests.Session.get")
    def test_get_user_info_success(self, mock_get, client):
        """Test successful retrieval of user information."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "accountId": "12345",
        }
        mock_get.return_value = mock_response

        user_info = client.get_user_info()

        assert user_info is not None
        assert user_info["displayName"] == "Test User"
        assert user_info["emailAddress"] == "test@example.com"
        assert user_info["accountId"] == "12345"

    @patch("jira_client.requests.Session.get")
    def test_get_user_info_failure(self, mock_get, client):
        """Test failure to retrieve user information."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        user_info = client.get_user_info()

        assert user_info is None

    @patch("jira_client.requests.Session.get")
    def test_get_user_info_exception(self, mock_get, client):
        """Test exception handling during user info retrieval."""
        mock_get.side_effect = Exception("Error")

        user_info = client.get_user_info()

        assert user_info is None


class TestJiraClientSessionManagement:
    """Test cases for session management."""

    @pytest.fixture
    def client(self):
        """Create a JiraClient instance for testing."""
        return JiraClient(
            base_url="https://test.atlassian.net", pat_token="test_token_123"
        )

    def test_close_session(self, client):
        """Test that session can be closed."""
        with patch.object(client.session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()

    def test_context_manager(self):
        """Test that JiraClient can be used as a context manager."""
        client = JiraClient(
            base_url="https://test.atlassian.net", pat_token="test_token"
        )
        with patch.object(client, "close") as mock_close:
            with client:
                pass
            mock_close.assert_called_once()


class TestJiraClientFactory:
    """Test cases for the factory function."""

    @patch.dict(
        os.environ,
        {
            "JIRA_URL": "https://factory-test.atlassian.net",
            "JIRA_PAT_TOKEN": "factory_token",
        },
    )
    def test_create_jira_client_success(self):
        """Test successful creation of JiraClient from environment."""
        client = create_jira_client()
        assert client is not None
        assert isinstance(client, JiraClient)

    @patch.dict(os.environ, {}, clear=True)
    def test_create_jira_client_failure(self):
        """Test failure to create JiraClient when env vars are missing."""
        client = create_jira_client()
        assert client is None


class TestJiraClientIntegration:
    """Integration-style tests (still using mocks for external calls)."""

    @pytest.fixture
    def client(self):
        """Create a JiraClient instance for testing."""
        return JiraClient(
            base_url="https://test.atlassian.net", pat_token="test_token_123"
        )

    @patch("jira_client.requests.Session.get")
    def test_full_connection_flow(self, mock_get, client):
        """Test the full connection flow including user info."""
        # Mock server info response
        server_response = Mock()
        server_response.status_code = 200
        server_response.json.return_value = {
            "serverTitle": "Test JIRA",
            "version": "9.0.0",
            "deploymentType": "Cloud",
        }

        # Mock user info response
        user_response = Mock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "accountId": "12345",
        }

        # Configure mock to return different responses for different calls
        mock_get.side_effect = [server_response, user_response]

        # Test connection
        success, result = client.test_connection()
        assert success is True

        # Get user info
        user_info = client.get_user_info()
        assert user_info is not None
        assert user_info["displayName"] == "Test User"

        # Verify both endpoints were called
        assert mock_get.call_count == 2

