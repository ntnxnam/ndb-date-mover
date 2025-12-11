"""
Date Utility Functions

Functions for date formatting, parsing, and week slip calculations.

Author: NDB Date Mover Team
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def format_date(date_str: str, target_format: str = "mm/dd/yyyy") -> str:
    """
    Format a date string to the target format.
    
    Args:
        date_str: Date string in various formats (ISO, JIRA format, etc.)
        target_format: Target format (mm/dd/yyyy, yyyy-mm-dd, dd/mm/yyyy)
        
    Returns:
        str: Formatted date string
    """
    if not date_str:
        return ""
    
    # Try to parse common date formats
    date_formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO with timezone
        "%Y-%m-%dT%H:%M:%S%z",      # ISO with timezone (no microseconds)
        "%Y-%m-%dT%H:%M:%S",         # ISO without timezone
        "%Y-%m-%d",                  # Simple date
        "%d/%m/%Y",                  # DD/MM/YYYY
        "%m/%d/%Y",                  # MM/DD/YYYY
    ]
    
    parsed_date = None
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue
    
    if not parsed_date:
        logger.warning(f"Could not parse date: {date_str}")
        return date_str  # Return original if parsing fails
    
    # Format to target format
    if target_format == "mm/dd/yyyy":
        return parsed_date.strftime("%m/%d/%Y")
    elif target_format == "yyyy-mm-dd":
        return parsed_date.strftime("%Y-%m-%d")
    elif target_format == "dd/mm/yyyy":
        return parsed_date.strftime("%d/%m/%Y")
    else:
        # Default to mm/dd/yyyy
        return parsed_date.strftime("%m/%d/%Y")


def calculate_week_slip(original_date: str, current_date: str) -> Tuple[int, str]:
    """
    Calculate the calendar week slip between two dates.
    
    Args:
        original_date: Original date (first in history) as string
        current_date: Current date as string
        
    Returns:
        Tuple[int, str]: (weeks, formatted_string)
            - weeks: Number of weeks (positive = delay, negative = ahead)
            - formatted_string: Human-readable string (e.g., "+3 weeks", "-1 week")
    """
    if not original_date or not current_date:
        return 0, "N/A"
    
    try:
        # Parse dates
        orig = parse_date(original_date)
        curr = parse_date(current_date)
        
        if not orig or not curr:
            return 0, "N/A"
        
        # Calculate difference
        delta = curr - orig
        days = delta.days
        
        # Convert to calendar weeks (round to nearest week)
        # A week is 7 days, so we divide by 7 and round
        weeks = round(days / 7)
        
        # Format string
        if weeks > 0:
            week_str = f"+{weeks} week{'s' if weeks != 1 else ''}"
        elif weeks < 0:
            week_str = f"{weeks} week{'s' if abs(weeks) != 1 else ''}"
        else:
            week_str = "0 weeks"
        
        return weeks, week_str
        
    except Exception as e:
        logger.error(f"Error calculating week slip: {str(e)}")
        return 0, "Error"


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string to datetime object.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Optional[datetime]: Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None
    
    date_formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def extract_date_history(
    changelog: List[Dict], field_id: str
) -> List[Tuple[str, str]]:
    """
    Extract date change history for a specific field from changelog.
    
    Args:
        changelog: List of change entries from JIRA changelog
        field_id: Field ID to extract history for
        
    Returns:
        List[Tuple[str, str]]: List of (date_value, timestamp) tuples,
                              sorted chronologically (oldest first)
    """
    dates = []
    
    for change in changelog:
        if change.get("field") == field_id:
            to_value = change.get("to")
            timestamp = change.get("timestamp", "")
            
            if to_value:
                dates.append((to_value, timestamp))
    
    # Sort by timestamp (oldest first)
    dates.sort(key=lambda x: x[1] if x[1] else "")
    
    return dates


def get_week_slip_color(weeks: int) -> str:
    """
    Get color code for week slip display.
    
    Args:
        weeks: Number of weeks (positive = delay, negative = ahead)
        
    Returns:
        str: Color name for CSS
    """
    if weeks > 0:
        return "red"  # Delay
    elif weeks < 0:
        return "green"  # Ahead of schedule
    else:
        return "gray"  # No change

