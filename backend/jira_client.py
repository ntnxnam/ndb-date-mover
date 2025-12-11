"""
JIRA Client Module

This module provides a client for connecting to JIRA using Personal Access Token (PAT)
authentication via bearer token. It handles connection testing, error handling, and
logging.

Author: NDB Date Mover Team
"""

import logging
import os
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class JiraConnectionError(Exception):
    """Custom exception for JIRA connection errors."""

    pass


class JiraClient:
    """
    JIRA Client for connecting to JIRA using Personal Access Token (PAT).

    This client uses bearer token authentication to connect to JIRA instances.
    It provides methods to test connections and interact with JIRA APIs.

    Attributes:
        base_url (str): Base URL of the JIRA instance
        pat_token (str): Personal Access Token for authentication
        session (requests.Session): HTTP session for making requests
    """

    def __init__(self, base_url: Optional[str] = None, pat_token: Optional[str] = None):
        """
        Initialize the JIRA client.

        Args:
            base_url: JIRA base URL (e.g., https://your-domain.atlassian.net)
                     If not provided, will be read from JIRA_URL environment variable
            pat_token: Personal Access Token for authentication
                      If not provided, will be read from JIRA_PAT_TOKEN environment variable

        Raises:
            ValueError: If base_url or pat_token is not provided and not in environment
        """
        self.base_url = base_url or os.getenv("JIRA_URL")
        self.pat_token = pat_token or os.getenv("JIRA_PAT_TOKEN")

        if not self.base_url:
            raise ValueError(
                "JIRA_URL must be provided either as parameter or environment variable"
            )
        if not self.pat_token:
            raise ValueError(
                "JIRA_PAT_TOKEN must be provided either as parameter or environment variable"
            )

        # Ensure base_url doesn't end with a slash
        self.base_url = self.base_url.rstrip("/")

        # Validate URL format
        parsed_url = urlparse(self.base_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid JIRA URL format: {self.base_url}")

        # Create a session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.pat_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        # Set default timeout for all requests (can be overridden per request)
        self.timeout = 10

        logger.info(f"JiraClient initialized for base URL: {self.base_url}")

    def test_connection(self) -> Tuple[bool, Dict]:
        """
        Test the connection to JIRA by making an API call.

        This method attempts to connect to JIRA and retrieve server information
        to verify that the authentication is working correctly.

        Returns:
            Tuple[bool, Dict]: A tuple containing:
                - bool: True if connection is successful, False otherwise
                - Dict: Response data or error information

        Example:
            >>> client = JiraClient()
            >>> success, data = client.test_connection()
            >>> if success:
            ...     print(f"Connected to {data.get('serverTitle')}")
        """
        logger.info("Testing JIRA connection...")

        # Use the /rest/api/3/serverInfo endpoint to test connection
        endpoint = "/rest/api/3/serverInfo"
        url = urljoin(self.base_url, endpoint)

        try:
            logger.debug(f"Making GET request to: {url}")
            response = self.session.get(url, timeout=self.timeout)

            # Log response details
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"Successfully connected to JIRA: {data.get('serverTitle', 'Unknown')}"
                )
                logger.info(f"JIRA version: {data.get('version', 'Unknown')}")
                return True, {
                    "success": True,
                    "message": "Connection successful",
                    "server_title": data.get("serverTitle"),
                    "version": data.get("version"),
                    "deployment_type": data.get("deploymentType"),
                }
            elif response.status_code == 401:
                logger.error("Authentication failed: Invalid or expired token")
                return False, {
                    "success": False,
                    "message": "Authentication failed: Invalid or expired token",
                    "status_code": response.status_code,
                }
            elif response.status_code == 403:
                logger.error("Authorization failed: Token lacks required permissions")
                return False, {
                    "success": False,
                    "message": "Authorization failed: Token lacks required permissions",
                    "status_code": response.status_code,
                }
            else:
                logger.error(
                    f"Connection failed with status code: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", "Unknown error")
                except ValueError:
                    error_message = response.text or "Unknown error"

                return False, {
                    "success": False,
                    "message": f"Connection failed: {error_message}",
                    "status_code": response.status_code,
                }

        except requests.exceptions.Timeout:
            logger.error("Connection timeout: JIRA server did not respond in time")
            return False, {
                "success": False,
                "message": "Connection timeout: JIRA server did not respond in time",
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: Unable to reach JIRA server - {str(e)}")
            return False, {
                "success": False,
                "message": f"Connection error: Unable to reach JIRA server - {str(e)}",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception occurred: {str(e)}")
            return False, {
                "success": False,
                "message": f"Request failed: {str(e)}",
            }
        except Exception as e:
            logger.exception("Unexpected error during connection test")
            return False, {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
            }

    def get_user_info(self) -> Optional[Dict]:
        """
        Get information about the authenticated user.

        Returns:
            Optional[Dict]: User information if successful, None otherwise
        """
        logger.info("Retrieving authenticated user information...")
        endpoint = "/rest/api/3/myself"
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Retrieved user info for: {user_data.get('displayName')}")
                return user_data
            else:
                logger.warning(
                    f"Failed to retrieve user info: Status {response.status_code}"
                )
                return None
        except Exception as e:
            logger.error(f"Error retrieving user info: {str(e)}")
            return None

    def close(self):
        """
        Close the HTTP session.

        This should be called when the client is no longer needed to free up resources.
        """
        logger.info("Closing JIRA client session")
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically closes session."""
        self.close()
        return False


def create_jira_client() -> Optional[JiraClient]:
    """
    Factory function to create a JiraClient instance from environment variables.

    Returns:
        Optional[JiraClient]: JiraClient instance if environment variables are set,
                            None otherwise
    """
    try:
        return JiraClient()
    except ValueError as e:
        logger.error(f"Failed to create JiraClient: {str(e)}")
        return None

