"""
Unit tests for Flask Application

This test suite covers:
- Flask routes
- API endpoints
- Error handling

Author: NDB Date Mover Team
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

# Add project root and backend to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Import the backend app
from backend.app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


class TestFlaskRoutes:
    """Test cases for Flask routes."""

    def test_root_route_not_found(self, client):
        """Test that the root route returns 404 (backend is API-only)."""
        # Backend is API-only, so root route should return 404
        response = client.get("/")
        assert response.status_code == 404

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "jira-connection-tester"


class TestConnectionEndpoint:
    """Test cases for the connection test endpoint."""

    @patch("backend.app.create_jira_client")
    def test_connection_success(self, mock_create_client, client):
        """Test successful connection test."""
        # Mock JIRA client
        mock_client = Mock()
        mock_client.test_connection.return_value = (
            True,
            {
                "success": True,
                "message": "Connection successful",
                "server_title": "Test JIRA",
                "version": "9.0.0",
            },
        )
        mock_client.get_user_info.return_value = {
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "accountId": "12345",
        }
        mock_create_client.return_value = mock_client

        response = client.post("/api/test-connection")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "Connection successful" in data["message"]
        assert data["server_title"] == "Test JIRA"
        assert "user" in data
        assert data["user"]["display_name"] == "Test User"

    @patch("backend.app.create_jira_client")
    def test_connection_failure(self, mock_create_client, client):
        """Test failed connection test."""
        # Mock JIRA client
        mock_client = Mock()
        mock_client.test_connection.return_value = (
            False,
            {
                "success": False,
                "message": "Authentication failed",
                "status_code": 401,
            },
        )
        mock_create_client.return_value = mock_client

        response = client.post("/api/test-connection")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Authentication failed" in data["message"]

    @patch("backend.app.create_jira_client")
    def test_connection_missing_credentials(self, mock_create_client, client):
        """Test connection test when credentials are missing."""
        mock_create_client.return_value = None

        response = client.post("/api/test-connection")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "not configured" in data["message"].lower()

    @patch("backend.app.create_jira_client")
    def test_connection_exception(self, mock_create_client, client):
        """Test connection test when an exception occurs."""
        mock_create_client.side_effect = Exception("Unexpected error")

        response = client.post("/api/test-connection")
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "Unexpected error" in data["message"]

    @patch("backend.app.create_jira_client")
    def test_connection_no_user_info(self, mock_create_client, client):
        """Test connection when user info is not available."""
        mock_client = Mock()
        mock_client.test_connection.return_value = (
            True,
            {
                "success": True,
                "message": "Connection successful",
                "server_title": "Test JIRA",
            },
        )
        mock_client.get_user_info.return_value = None
        mock_create_client.return_value = mock_client

        response = client.post("/api/test-connection")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "user" not in data

