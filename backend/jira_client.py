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

from .utils import safe_get_response_text, check_html_response

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
                
                # Don't retry on authentication/authorization errors (401, 403) - these won't succeed
                if response.status_code in [401, 403]:
                    logger.error(f"Authentication/authorization error {response.status_code}, not retrying")
                    self._session_stale = False
                    return response
                
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

        # Use the /rest/api/2/serverInfo endpoint to test connection
        # Note: Some JIRA instances (like Nutanix) use API v2, not v3
        endpoint = "/rest/api/2/serverInfo"
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
        endpoint = "/rest/api/2/myself"
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
                    safe_get_response_text(response, 200)  # Log for debugging
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
        
        # Handle filter reference format
        # Support:
        # - filter=12345 (numeric filter ID)
        # - filter = 12345 (with spaces)
        # - filter="Filter Name" (named filter with quotes)
        # - filter=FilterName (named filter without spaces)
        # - filter = "Filter Name" (with spaces)
        # - filter=12345 AND additional clauses (filter with additional JQL)
        import re
        jql_stripped = jql.strip()
        
        # Match filter= or filter = (case insensitive, with optional spaces)
        filter_match = re.match(r'^filter\s*=\s*(.+)$', jql_stripped, re.IGNORECASE)
        if filter_match:
            # Extract filter reference and any additional JQL
            filter_part = filter_match.group(1).strip()
            
            # Check if there's additional JQL after the filter
            # Look for AND/OR/ORDER BY keywords that indicate additional clauses
            additional_jql = None
            filter_id_or_name = filter_part
            
            # Try to split on AND/OR/ORDER BY (case insensitive)
            # Match patterns:
            # - " and " or " AND " or " or " or " OR " with spaces
            # - " order by " or " ORDER BY " with spaces
            # This ensures we don't match keywords inside words
            # Priority: ORDER BY first (it's more specific), then AND/OR
            match = None
            # First try ORDER BY (more specific, usually comes at the end)
            order_by_match = re.search(r'\s+ORDER\s+BY\s+', filter_part, re.IGNORECASE)
            if order_by_match:
                match = order_by_match
            else:
                # Then try AND/OR
                match = re.search(r'\s+(AND|OR)\s+', filter_part, re.IGNORECASE)
            
            if match:
                split_pos = match.start()
                filter_id_or_name = filter_part[:split_pos].strip()
                additional_jql = filter_part[split_pos:].strip()
                # Normalize keywords to uppercase for consistency
                additional_jql = re.sub(r'\b(and|or)\b', lambda m: m.group(1).upper(), additional_jql, flags=re.IGNORECASE)
                additional_jql = re.sub(r'\b(order\s+by)\b', 'ORDER BY', additional_jql, flags=re.IGNORECASE)
            
            # Remove quotes if present for processing, but preserve them if they were there
            is_quoted = False
            if filter_id_or_name.startswith('"') and filter_id_or_name.endswith('"'):
                is_quoted = True
                filter_id_or_name = filter_id_or_name[1:-1].strip()  # Remove quotes
            
            # Handle numeric filter ID
            if filter_id_or_name.isdigit():
                jql = f"filter = {filter_id_or_name}"
                if additional_jql:
                    jql = f"{jql} {additional_jql}"
                logger.info(f"Converted numeric filter ID {filter_id_or_name} to JQL: {jql}")
            # Handle named filter
            else:
                # If it was quoted or contains spaces/special chars, quote it
                if is_quoted or ' ' in filter_id_or_name or not filter_id_or_name.replace('_', '').replace('-', '').isalnum():
                    jql = f'filter = "{filter_id_or_name}"'
                else:
                    # Simple name without spaces - can be unquoted or quoted (JIRA accepts both)
                    # Quote it for safety
                    jql = f'filter = "{filter_id_or_name}"'
                
                if additional_jql:
                    jql = f"{jql} {additional_jql}"
                logger.info(f"Converted filter name to JQL: {jql}")
        
        endpoint = "/rest/api/2/search"
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
                # Check for HTML responses BEFORE attempting JSON parse
                # HTML usually indicates auth failure, invalid URL, or permission issues
                if "text/html" in content_type:
                    response_text = getattr(response, 'text', '') or str(getattr(response, 'content', ''))[:500]
                    logger.error(f"JIRA returned HTML instead of JSON. This usually indicates:")
                    logger.error("  1. Authentication failure (redirected to login page)")
                    logger.error("  2. Invalid JIRA URL")
                    logger.error("  3. Insufficient permissions for the filter/query")
                    logger.debug(f"Response preview: {response_text}")
                    return {
                        "success": False,
                        "error": "JIRA returned an HTML page instead of JSON. This usually means:\n"
                                "- Authentication failed (check your JIRA_PAT_TOKEN)\n"
                                "- Invalid JIRA URL (check your JIRA_URL)\n"
                                "- Insufficient permissions for this filter/query\n"
                                "Please verify your credentials and JIRA URL in the .env file.",
                        "issues": [],
                        "total": 0,
                    }
                
                # Now safe to attempt JSON parsing
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response from JIRA: {str(e)}")
                    response_text = getattr(response, 'text', '') or str(getattr(response, 'content', ''))[:500]
                    logger.debug(f"Response text: {response_text}")
                    logger.debug(f"Content-Type: {content_type}")
                    return {
                        "success": False,
                        "error": f"JIRA returned invalid response format. Please check your JIRA URL and connection. Response preview: {response_text[:200]}",
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
        endpoint = "/rest/api/2/field"
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self._make_request_with_retry("GET", url)
            
            if response.status_code == 200:
                # Check content type before parsing
                content_type = response.headers.get("content-type", "").lower()
                try:
                    all_fields = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response from JIRA field metadata: {str(e)}")
                    response_text = safe_get_response_text(response, 500)
                    if response_text:
                        logger.debug(f"Response text: {response_text}")
                    logger.debug(f"Content-Type: {content_type}")
                    return {}
                
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
        
        Uses the expand=changelog parameter which is more reliable than the /changelog endpoint.
        Handles both response formats for compatibility.
        
        According to JIRA API v2 documentation:
        - Changelog items may or may not include "fieldId"
        - Items always include "field" (field name) and "fieldtype"
        - For custom fields, fieldId may be numeric (e.g., 11067) or customfield_ format
        - When fieldId is missing, we resolve it from field metadata using field name
        
        Args:
            issue_id: JIRA issue key (e.g., "PROJ-123")
            field_id: Optional specific field ID to filter changes (e.g., "customfield_11067")
            
        Returns:
            List[Dict]: List of changes, each containing:
                - field: Field ID that changed (normalized to customfield_ format if numeric)
                - field_original: Original fieldId from changelog (may be None)
                - field_name: Human-readable field name
                - fieldtype: Field type (e.g., "custom", "jira")
                - from: Previous value (fromString)
                - to: New value (toString)
                - timestamp: When change occurred
        """
        logger.debug(f"Fetching changelog for issue: {issue_id} (field_id: {field_id})")
        
        # Use expand=changelog which is more reliable than /changelog endpoint
        # Some JIRA instances don't support the /changelog endpoint but support expand
        endpoint = f"/rest/api/2/issue/{issue_id}"
        url = urljoin(self.base_url, endpoint)
        
        params = {"expand": "changelog", "maxResults": 1000}  # Get all changes
        
        # Get field metadata to resolve field IDs from names when needed
        field_metadata = None
        field_name_to_id = {}
        try:
            field_metadata = self.get_field_metadata()
            if field_metadata:
                # Build name-to-ID mapping for quick lookup
                for fid, field_data in field_metadata.items():
                    field_name = field_data.get("name", "")
                    if field_name:
                        field_name_to_id[field_name] = fid
                logger.debug(f"Built field name mapping with {len(field_name_to_id)} fields")
        except Exception as e:
            logger.warning(f"Could not fetch field metadata for changelog resolution: {str(e)}")
        
        try:
            # Changelog requests can take longer, use extended timeout
            # Temporarily increase timeout for this request
            original_timeout = self.timeout
            self.timeout = 30  # 30 seconds for changelog requests
            try:
                response = self._make_request_with_retry("GET", url, params=params)
            finally:
                self.timeout = original_timeout  # Restore original timeout
            
            if response.status_code == 200:
                # Check content type before parsing
                content_type = response.headers.get("content-type", "").lower()
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response from JIRA changelog: {str(e)}")
                    response_text = safe_get_response_text(response, 500)
                    if response_text:
                        logger.debug(f"Response text: {response_text}")
                    logger.debug(f"Content-Type: {content_type}")
                    return []
                
                # Handle both response formats:
                # 1. expand=changelog format: data['changelog']['histories']
                # 2. /changelog endpoint format: data['values'] (fallback)
                changelog_data = data.get("changelog", {})
                if changelog_data:
                    histories = changelog_data.get("histories", [])
                else:
                    # Fallback to direct /changelog endpoint format
                    histories = data.get("values", [])
                
                if not histories:
                    logger.debug(f"No changelog history found for issue {issue_id}")
                    return []
                
                # Extract changes
                changes = []
                for history in histories:
                    created = history.get("created", "")
                    items = history.get("items", [])
                    
                    for item in items:
                        # JIRA API v2 changelog structure:
                        # - item.get("fieldId") may be None, numeric (e.g., 11067), or customfield_ format
                        # - item.get("field") is the field name (e.g., "Code Complete Date")
                        # - item.get("fieldtype") indicates field type (e.g., "custom", "jira")
                        
                        change_field_id = item.get("fieldId")
                        field_name = item.get("field", "")
                        field_type = item.get("fieldtype", "")
                        
                        # Resolve field ID if missing
                        resolved_field_id = change_field_id
                        if not resolved_field_id and field_name and field_name_to_id:
                            # Try to resolve from field metadata
                            resolved_field_id = field_name_to_id.get(field_name)
                            if resolved_field_id:
                                logger.debug(f"Resolved field ID for '{field_name}': {resolved_field_id}")
                        
                        # Normalize fieldId: convert numeric IDs to customfield_ format
                        # JIRA changelog may return numeric IDs (e.g., "11067") but we need "customfield_11067"
                        normalized_field_id = self._normalize_field_id(resolved_field_id) if resolved_field_id else field_name
                        
                        # Filter by field_id if provided
                        # Match by: normalized ID, original ID, numeric ID, or resolved ID
                        if field_id:
                            field_id_match = (
                                normalized_field_id == field_id or
                                resolved_field_id == field_id or
                                change_field_id == field_id or
                                (change_field_id and str(change_field_id) == field_id.replace("customfield_", "")) or
                                (resolved_field_id and str(resolved_field_id) == field_id.replace("customfield_", ""))
                            )
                            if not field_id_match:
                                continue
                        
                        changes.append({
                            "field": normalized_field_id,  # Use normalized format or field name
                            "field_original": change_field_id,  # Keep original for reference (may be None)
                            "field_resolved": resolved_field_id,  # Resolved from metadata if original was None
                            "field_name": field_name,
                            "fieldtype": field_type,
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
    
    def _normalize_field_id(self, field_id) -> str:
        """
        Normalize field ID to standard format.
        
        JIRA changelog may return numeric IDs for custom fields (e.g., "11067")
        but we need the standard format (e.g., "customfield_11067").
        
        Args:
            field_id: Field ID from changelog (may be numeric, string, or customfield_ format)
            
        Returns:
            str: Normalized field ID in customfield_ format if numeric, otherwise original
        """
        if not field_id:
            return field_id
        
        field_id_str = str(field_id)
        
        # If it's a numeric string and looks like a custom field ID, convert to customfield_ format
        # Custom field IDs are typically 5+ digits
        if field_id_str.isdigit() and len(field_id_str) >= 4:
            return f"customfield_{field_id_str}"
        
        # If already in customfield_ format, return as-is
        if field_id_str.startswith("customfield_"):
            return field_id_str
        
        # For standard fields (key, summary, status, etc.), return as-is
        return field_id_str
    
    def _match_field_by_name(self, field_name: str, target_field_id: str) -> bool:
        """
        Try to match a field by name when fieldId is not available in changelog.
        
        This is a fallback when JIRA changelog doesn't include fieldId.
        We would need field metadata to do proper matching, but for now
        this is a simple check.
        
        Args:
            field_name: Field name from changelog
            target_field_id: Target field ID to match against
            
        Returns:
            bool: True if likely a match (basic heuristic)
        """
        # This is a basic heuristic - in practice, you'd need to look up
        # field metadata to match name to ID
        # For now, return False to be safe (caller should use field metadata)
        return False

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

