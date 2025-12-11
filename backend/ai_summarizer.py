"""
AI Summarizer Module

Provides functionality to summarize text content in an executive-friendly format.

Author: NDB Date Mover Team
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def summarize_for_executives(text: str, max_length: int = 200) -> str:
    """
    Summarize text content in an executive-friendly format.
    
    This function provides a simple rule-based summarization. For production use,
    you may want to integrate with an AI service (OpenAI, Anthropic, etc.).
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary
        
    Returns:
        str: Executive-friendly summary
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # If text is already short, return as-is
    if len(text) <= max_length:
        return text
    
    # Simple summarization: take first sentence or first N characters
    # For better results, consider integrating with OpenAI/Anthropic API
    sentences = text.split('. ')
    if sentences and len(sentences[0]) <= max_length:
        summary = sentences[0]
        if not summary.endswith('.'):
            summary += '.'
        return summary
    
    # Fallback: truncate with ellipsis
    summary = text[:max_length - 3].rsplit(' ', 1)[0] + '...'
    return summary


def summarize_status_update(status_text: str) -> str:
    """
    Summarize a status update field in an executive-friendly format.
    
    Args:
        status_text: The status update text to summarize
        
    Returns:
        str: Executive-friendly summary
    """
    if not status_text:
        return ""
    
    # Clean the text
    text = str(status_text).strip()
    
    # Remove common prefixes/suffixes that aren't useful
    prefixes_to_remove = [
        "Status:",
        "Update:",
        "Note:",
        "Comment:",
    ]
    
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    # Summarize to executive-friendly length (150-200 chars)
    return summarize_for_executives(text, max_length=200)

