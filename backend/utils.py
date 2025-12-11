"""
Shared utility functions for JIRA client error handling.

Author: NDB Date Mover Team
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def safe_get_response_text(response, max_length: int = 500) -> str:
    """
    Safely extract text from a response object, handling Mock objects in tests.
    
    Args:
        response: Response object (requests.Response or Mock)
        max_length: Maximum length of text to return
        
    Returns:
        str: Response text (truncated if needed), empty string if unavailable
    """
    try:
        text = getattr(response, 'text', '')
        if text:
            return text[:max_length] if len(text) > max_length else text
        # Fallback to content if text not available
        content = getattr(response, 'content', b'')
        if content:
            return str(content[:max_length])
    except Exception as e:
        logger.debug(f"Error extracting response text: {str(e)}")
    return ''


def check_html_response(content_type: str, response) -> Optional[str]:
    """
    Check if response is HTML and return appropriate error message.
    
    Args:
        content_type: Content-Type header value
        response: Response object
        
    Returns:
        Optional[str]: Error message if HTML detected, None otherwise
    """
    if "text/html" in content_type.lower():
        response_text = safe_get_response_text(response, 500)
        logger.error("JIRA returned HTML instead of JSON. This usually indicates:")
        logger.error("  1. Authentication failure (redirected to login page)")
        logger.error("  2. Invalid JIRA URL")
        logger.error("  3. Insufficient permissions for the filter/query")
        logger.debug(f"Response preview: {response_text}")
        return (
            "JIRA returned an HTML page instead of JSON. This usually means:\n"
            "- Authentication failed (check your JIRA_PAT_TOKEN)\n"
            "- Invalid JIRA URL (check your JIRA_URL)\n"
            "- Insufficient permissions for this filter/query\n"
            "Please verify your credentials and JIRA URL in the .env file."
        )
    return None

