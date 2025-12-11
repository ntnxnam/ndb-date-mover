"""
Date Utility Functions

Functions for date formatting, parsing, and week slip calculations.

Author: NDB Date Mover Team
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def format_date(date_str: str, target_format: str = "dd/mmm/yyyy") -> str:
    """
    Format a date string to the target format.
    
    Accepts JIRA-friendly formats (ISO 8601) internally and converts to display format.
    Display format is always dd/mmm/yyyy (e.g., 15/Jan/2026) regardless of config.
    
    Args:
        date_str: Date string in JIRA-friendly formats (ISO 8601, etc.)
        target_format: Target format (ignored - always uses dd/mmm/yyyy for display)
        
    Returns:
        str: Formatted date string in dd/mmm/yyyy format (e.g., 15/Jan/2026)
    """
    if not date_str:
        return ""
    
    # Month abbreviations mapping
    month_abbr = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    
    # Try to parse common date formats
    date_formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO with timezone
        "%Y-%m-%dT%H:%M:%S%z",      # ISO with timezone (no microseconds)
        "%Y-%m-%dT%H:%M:%S",         # ISO without timezone
        "%Y-%m-%d",                  # Simple date
        "%d/%m/%Y",                  # DD/MM/YYYY (numeric month)
        "%m/%d/%Y",                  # MM/DD/YYYY (numeric month)
        "%d/%b/%Y",                  # DD/Mmm/YYYY (e.g., 13/Jun/2025)
        "%d/%b/%y",                  # DD/Mmm/YY (e.g., 13/Jun/25)
    ]
    
    parsed_date = None
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue
    
    # Try manual parsing for dd/mmm/yyyy format if standard formats fail
    # This handles cases where dates are already in display format
    if not parsed_date:
        try:
            import re
            month_map = {
                "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
            }
            match = re.match(r'^(\d{1,2})/([A-Za-z]{3})/(\d{2,4})$', date_str.strip())
            if match:
                day = int(match.group(1))
                month_str = match.group(2).capitalize()
                year_str = match.group(3)
                
                if month_str in month_map:
                    month = month_map[month_str]
                    # Handle 2-digit vs 4-digit year
                    if len(year_str) == 2:
                        year = 2000 + int(year_str) if int(year_str) < 50 else 1900 + int(year_str)
                    else:
                        year = int(year_str)
                    
                    parsed_date = datetime(year, month, day)
        except (ValueError, AttributeError):
            pass
    
    if not parsed_date:
        logger.warning(f"Could not parse date: {date_str}")
        return date_str  # Return original if parsing fails
    
    # Format to dd/mmm/yyyy (e.g., 15/Jan/2026)
    day = parsed_date.day
    month = month_abbr[parsed_date.month]
    year = parsed_date.year
    return f"{day:02d}/{month}/{year}"


def calculate_week_slip(original_date: str, current_date: str) -> Tuple[int, str]:
    """
    Calculate the calendar week slip between two dates.
    
    Uses the new date_display module for consistent formatting.
    
    Args:
        original_date: Original date (first in history) as string
        current_date: Current date as string
        
    Returns:
        Tuple[int, str]: (weeks, formatted_string)
            - weeks: Number of weeks (positive = delay, negative = ahead) - rounded for backward compatibility
            - formatted_string: Human-readable string (e.g., "+3 days", "+1.5 weeks", "-1 week")
    """
    from backend.date_display import calculate_date_difference_display
    
    if not original_date or not current_date:
        return 0, "N/A"
    
    try:
        # Use the new date display module
        display_str, unit_type = calculate_date_difference_display(original_date, current_date)
        
        # For backward compatibility, calculate weeks as integer
        orig = parse_date(original_date)
        curr = parse_date(current_date)
        
        if not orig or not curr:
            return 0, display_str
        
        delta = curr - orig
        days = delta.days
        weeks = round(days / 7)  # Integer weeks for backward compatibility
        
        return weeks, display_str
        
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

