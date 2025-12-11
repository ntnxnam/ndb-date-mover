"""
JIRA Client Module

This module provides a client for connecting to JIRA using Personal Access Token (PAT)
authentication via bearer token. It handles connection testing, error handling, and
logging.

Author: NDB Date Mover Team
"""

import logging
import os
import time
from typing import Dict, List, Optional, Tuple
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
        self._session_stale = False

        # Set default timeout for all requests (can be overridden per request)
        self.timeout = 10
        
        # Self-healing configuration
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff in seconds
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutes

        logger.info(f"JiraClient initialized for base URL: {self.base_url}")

    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with automatic retry and self-healing.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response: Response object
            
        Raises:
            requests.exceptions.RequestException: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Check if we need to refresh the session
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{self.max_retries} for {url}")
                    # Recreate session if connection seems stale
                    if hasattr(self, '_session_stale') and self._session_stale:
                        logger.info("Recreating session due to stale connection")
                        self.session.close()
                        self.session = requests.Session()
                        self.session.headers.update({
                            "Authorization": f"Bearer {self.pat_token}",
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        })
                        self._session_stale = False
                    
                    # Exponential backoff
                    if attempt <= len(self.retry_delays):
                        delay = self.retry_delays[attempt - 1]
                        logger.debug(f"Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                
                # Make the request
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                
                # If successful, mark session as healthy
                if response.status_code < 500:
                    self._session_stale = False
                    return response
                    
                # For 5xx errors, retry
                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, will retry")
                    last_exception = requests.exceptions.HTTPError(f"HTTP {response.status_code}")
                    continue
                    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
                self._session_stale = True
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise
            except requests.exceptions.RequestException as e:
                last_exception = e
                # Don't retry for client errors (4xx)
                if hasattr(e, 'response') and e.response and 400 <= e.response.status_code < 500:
                    raise
                logger.warning(f"Request error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise requests.exceptions.RequestException("All retry attempts failed")

    def test_connection(self) -> Tuple[bool, Dict]:
        """
        Test the connection to JIRA by making an API call.

        This method attempts to connect to JIRA and retrieve server information
        to verify that the authentication is working correctly.
        Includes automatic retry and self-healing for transient failures.

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
            response = self._make_request_with_retry("GET", url)

            # Log response details
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response from JIRA: {str(e)}")
                    logger.debug(f"Response text: {response.text[:200]}")
                    return False, {
                        "success": False,
                        "message": "JIRA returned invalid response format. Please check your JIRA URL and connection.",
                    }
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
                
                # Try to extract error message from response
                error_message = "Unknown error"
                content_type = response.headers.get("content-type", "").lower()
                
                if "application/json" in content_type:
                    try:
                        error_data = response.json()
                        error_message = error_data.get("message") or error_data.get("error") or "Unknown error"
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Failed to parse error response as JSON: {str(e)}")
                        # Try to get text response
                        error_message = response.text[:200] if response.text else "Unknown error"
                else:
                    # Not JSON, get text response
                    error_message = response.text[:200] if response.text else f"HTTP {response.status_code} error"

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
            error_msg = str(e)
            # Provide more user-friendly error messages
            if "Expecting value" in error_msg or "JSON" in error_msg:
                error_msg = "JIRA returned an invalid response. Please verify your JIRA URL and credentials."
            logger.error(f"Request exception occurred: {error_msg}")
            return False, {
                "success": False,
                "message": f"Request failed: {error_msg}",
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
            response = self._make_request_with_retry("GET", url)
            if response.status_code == 200:
                try:
                    user_data = response.json()
                    logger.info(f"Retrieved user info for: {user_data.get('displayName')}")
                    return user_data
                except ValueError as e:
                    logger.error(f"Failed to parse user info JSON: {str(e)}")
                    return None
            else:
                logger.warning(
                    f"Failed to retrieve user info: Status {response.status_code}"
                )
                return None
        except Exception as e:
            logger.error(f"Error retrieving user info: {str(e)}")
            return None

    def execute_jql(self, jql: str, max_results: int = 100, start_at: int = 0) -> Dict:
        """
        Execute a JQL query against JIRA.
        
        Supports both standard JQL and filter IDs (e.g., filter=12345).
        
        Args:
            jql: JQL query string or filter ID (filter=xxxxx)
            max_results: Maximum number of results to return (default: 100)
            start_at: Starting index for pagination (default: 0)
            
        Returns:
            Dict: Query results with issues and metadata
            
        Raises:
            requests.exceptions.RequestException: If query execution fails
        """
        logger.info(f"Executing JQL query: {jql[:100]}...")
        
        # Handle filter ID format
        if jql.strip().startswith("filter="):
            filter_id = jql.strip().replace("filter=", "").strip()
            jql = f"filter = {filter_id}"
            logger.info(f"Converted filter ID to JQL: {jql}")
        
        endpoint = "/rest/api/3/search"
        url = urljoin(self.base_url, endpoint)
        
        params = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start_at,
            "fields": "*all",  # Get all fields
        }
        
        try:
            response = self._make_request_with_retry("GET", url, params=params)
            
            # Check content type before parsing
            content_type = response.headers.get("content-type", "").lower()
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response from JIRA: {str(e)}")
                    logger.debug(f"Response text: {response.text[:500]}")
                    logger.debug(f"Content-Type: {content_type}")
                    return {
                        "success": False,
                        "error": f"JIRA returned invalid response format. Please check your JIRA URL and connection. Response preview: {response.text[:200]}",
                        "issues": [],
                        "total": 0,
                    }
                
                logger.info(
                    f"JQL query returned {len(data.get('issues', []))} issues "
                    f"(total: {data.get('total', 0)})"
                )
                return {
                    "success": True,
                    "issues": data.get("issues", []),
                    "total": data.get("total", 0),
                    "start_at": data.get("startAt", 0),
                    "max_results": data.get("maxResults", max_results),
                }
            elif response.status_code == 400:
                # JQL syntax error
                error_message = "Invalid JQL query syntax"
                if "application/json" in content_type:
                    try:
                        error_data = response.json()
                        error_messages = error_data.get("errorMessages", [])
                        error_message = error_messages[0] if error_messages else "Invalid JQL query"
                    except (ValueError, KeyError, IndexError) as e:
                        logger.warning(f"Failed to parse error response: {str(e)}")
                        error_message = response.text[:200] if response.text else "Invalid JQL query syntax"
                else:
                    # Not JSON, get text response
                    error_message = response.text[:200] if response.text else "Invalid JQL query syntax"
                
                logger.error(f"JQL syntax error: {error_message}")
                return {
                    "success": False,
                    "error": error_message,
                    "issues": [],
                    "total": 0,
                }
            else:
                logger.error(f"JQL query failed with status {response.status_code}")
                # Try to get error message
                error_message = f"Query failed with status {response.status_code}"
                if response.text:
                    try:
                        if "application/json" in content_type:
                            error_data = response.json()
                            error_message = error_data.get("message") or error_data.get("error") or error_message
                        else:
                            error_message = response.text[:200]
                    except (ValueError, KeyError):
                        pass
                
                return {
                    "success": False,
                    "error": error_message,
                    "issues": [],
                    "total": 0,
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            # Provide more user-friendly error messages
            if "Expecting value" in error_msg or "JSON" in error_msg:
                error_msg = "JIRA returned an invalid response. Please verify your JIRA URL and credentials."
            logger.error(f"Request exception during JQL execution: {error_msg}")
            return {
                "success": False,
                "error": f"Request failed: {error_msg}",
                "issues": [],
                "total": 0,
            }

    def get_field_metadata(self, field_id: Optional[str] = None) -> Dict:
        """
        Get field metadata from JIRA.
        
        Args:
            field_id: Specific field ID to fetch. If None, returns all fields.
            
        Returns:
            Dict: Field metadata. If field_id provided, returns single field.
                  If None, returns all fields as a dict keyed by field ID.
        """
        endpoint = "/rest/api/3/field"
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self._make_request_with_retry("GET", url)
            
            if response.status_code == 200:
                all_fields = response.json()
                
                # Convert to dict keyed by field ID for easy lookup
                fields_dict = {field["id"]: field for field in all_fields}
                
                if field_id:
                    field_data = fields_dict.get(field_id)
                    if field_data:
                        logger.info(f"Retrieved metadata for field: {field_id}")
                        return field_data
                    else:
                        logger.warning(f"Field {field_id} not found in JIRA")
                        return {}
                else:
                    logger.info(f"Retrieved metadata for {len(fields_dict)} fields")
                    return fields_dict
            else:
                logger.error(f"Failed to fetch field metadata: {response.status_code}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception fetching field metadata: {str(e)}")
            return {}

    def get_issue_changelog(
        self, issue_id: str, field_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get changelog (change history) for an issue.
        
        Args:
            issue_id: JIRA issue key (e.g., "PROJ-123")
            field_id: Optional specific field ID to filter changes
            
        Returns:
            List[Dict]: List of changes, each containing:
                - field: Field ID that changed
                - from: Previous value
                - to: New value
                - timestamp: When change occurred
        """
        logger.info(f"Fetching changelog for issue: {issue_id}")
        endpoint = f"/rest/api/3/issue/{issue_id}/changelog"
        url = urljoin(self.base_url, endpoint)
        
        params = {"maxResults": 1000}  # Get all changes
        
        try:
            response = self._make_request_with_retry("GET", url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                histories = data.get("values", [])
                
                # Extract changes
                changes = []
                for history in histories:
                    created = history.get("created", "")
                    for item in history.get("items", []):
                        change_field_id = item.get("fieldId")
                        
                        # Filter by field_id if provided
                        if field_id and change_field_id != field_id:
                            continue
                            
                        changes.append({
                            "field": change_field_id,
                            "field_name": item.get("field"),
                            "from": item.get("fromString"),
                            "to": item.get("toString"),
                            "timestamp": created,
                        })
                
                logger.info(
                    f"Retrieved {len(changes)} changes for issue {issue_id}"
                    + (f" (filtered by {field_id})" if field_id else "")
                )
                return changes
            elif response.status_code == 404:
                logger.warning(f"Issue {issue_id} not found")
                return []
            else:
                logger.error(
                    f"Failed to fetch changelog: {response.status_code}"
                )
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception fetching changelog: {str(e)}")
            return []

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

