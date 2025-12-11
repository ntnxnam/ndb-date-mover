"""
Date Display Utility Module

Reusable module for calculating and displaying date differences in a human-readable format.
Can be used across different projects for date difference calculations.

Author: NDB Date Mover Team
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def calculate_date_difference_display(
    original_date: str, 
    current_date: str
) -> Tuple[str, str]:
    """
    Calculate the difference between two dates and return a human-readable display string.
    
    Rules:
    - If difference < 7 days: Show as "X days" (e.g., "3 days", "6 days")
    - If difference >= 7 days: Show in weeks with proper rounding:
      - 8 days = "1 week"
      - 9-11 days = "1.5 weeks"
      - 12 days = "1.5 weeks"
      - 13-14 days = "2 weeks"
      - 15-20 days = "2.5 weeks" (if applicable)
      - etc.
    
    Args:
        original_date: Original date (first in history) as string in various formats
        current_date: Current date as string in various formats
        
    Returns:
        Tuple[str, str]: (display_string, unit_type)
            - display_string: Human-readable string (e.g., "3 days", "1.5 weeks", "+2 weeks")
            - unit_type: Either "days" or "weeks"
    """
    if not original_date or not current_date:
        return "N/A", "unknown"
    
    try:
        # Parse dates
        orig = _parse_date(original_date)
        curr = _parse_date(current_date)
        
        if not orig or not curr:
            return "N/A", "unknown"
        
        # Calculate difference
        delta = curr - orig
        days = delta.days
        
        # Determine if ahead or behind
        sign = "+" if days >= 0 else "-"
        abs_days = abs(days)
        
        # Apply rules
        if abs_days < 7:
            # Show as days
            if abs_days == 0:
                return "0 days", "days"
            elif abs_days == 1:
                return f"{sign}1 day", "days"
            else:
                return f"{sign}{abs_days} days", "days"
        else:
            # Show as weeks with proper rounding
            weeks = _calculate_weeks_with_rounding(abs_days)
            
            if weeks == 1:
                return f"{sign}1 week", "weeks"
            elif weeks == 1.5:
                return f"{sign}1.5 weeks", "weeks"
            elif weeks == 2:
                return f"{sign}2 weeks", "weeks"
            elif weeks == 2.5:
                return f"{sign}2.5 weeks", "weeks"
            elif weeks == 3:
                return f"{sign}3 weeks", "weeks"
            else:
                # For larger values, round to nearest 0.5
                if weeks % 1 == 0:
                    return f"{sign}{int(weeks)} weeks", "weeks"
                else:
                    return f"{sign}{weeks} weeks", "weeks"
        
    except Exception as e:
        logger.error(f"Error calculating date difference display: {str(e)}")
        return "Error", "unknown"


def _calculate_weeks_with_rounding(days: int) -> float:
    """
    Calculate weeks from days with proper rounding rules.
    
    Rules (applied consistently across all week counts, following 1-2 week pattern):
    - For N weeks (integer, N >= 1): 
      - If N == 1: 7-8 days (1*7 to 1*7+1)
      - If N > 1: (N*7 - 1) to (N*7 + 1) days
      - Examples: 1 week: 7-8, 2 weeks: 13-15, 3 weeks: 20-22, 4 weeks: 27-29
    
    - For N.5 weeks (half): Range is (N*7 + 2) to ((N+1)*7 - 2) days
      - Examples: 1.5 weeks: 9-12, 2.5 weeks: 16-19, 3.5 weeks: 23-26, 4.5 weeks: 30-33
    
    Args:
        days: Number of days
        
    Returns:
        float: Number of weeks (can be 1, 1.5, 2, 2.5, 3, 3.5, etc.)
    """
    if days < 7:
        return 0
    
    # Calculate which week range this falls into
    exact_weeks = days / 7.0
    week_number = int(exact_weeks)
    
    # Special case for 1 week: 7-8 days
    if days <= 8:
        return 1.0
    
    # For each week number N (starting from 2):
    # - N weeks: (N*7 - 1) to (N*7 + 1) days
    # - N.5 weeks: (N*7 + 2) to ((N+1)*7 - 2) days
    
    # Check if days fall in integer week range (for N >= 2)
    lower_bound_integer = week_number * 7 - 1
    upper_bound_integer = week_number * 7 + 1
    
    if lower_bound_integer <= days <= upper_bound_integer:
        return float(week_number)
    
    # Check if days fall in half week range (N.5 weeks)
    lower_bound_half = week_number * 7 + 2
    upper_bound_half = (week_number + 1) * 7 - 2
    
    if lower_bound_half <= days <= upper_bound_half:
        return float(week_number) + 0.5
    
    # If we're between ranges, check next integer week
    if days > upper_bound_half and days < (week_number + 1) * 7 - 1:
        return float(week_number + 1)
    
    # Fallback: round to nearest 0.5
    return round(exact_weeks * 2) / 2.0


def _parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string to datetime object.
    
    Supports multiple date formats including the display format (dd/mmm/yyyy).
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Optional[datetime]: Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None
    
    # Month abbreviations mapping (for parsing dd/mmm/yyyy format)
    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }
    
    date_formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO with timezone and microseconds
        "%Y-%m-%dT%H:%M:%S%z",      # ISO with timezone (no microseconds)
        "%Y-%m-%dT%H:%M:%S",         # ISO without timezone
        "%Y-%m-%d",                  # Simple date
        "%d/%m/%Y",                  # DD/MM/YYYY (numeric month)
        "%m/%d/%Y",                  # MM/DD/YYYY (numeric month)
        "%d/%b/%Y",                  # DD/Mmm/YYYY (e.g., 13/Jun/2025)
        "%d/%b/%y",                  # DD/Mmm/YY (e.g., 13/Jun/25)
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try manual parsing for dd/mmm/yyyy format if standard formats fail
    # This handles cases like "13/Jun/2025" or "13/Jun/25"
    try:
        # Pattern: dd/mmm/yyyy or dd/mmm/yy
        import re
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
                
                return datetime(year, month, day)
    except (ValueError, AttributeError):
        pass
    
    return None


def normalize_date_for_comparison(date_str: str) -> Optional[str]:
    """
    Normalize a date string to a standard format for comparison.
    
    This is useful when comparing dates from different sources (JIRA changelog vs current value)
    that might be in different formats.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Optional[str]: Normalized date string in YYYY-MM-DD format, or None if parsing fails
    """
    parsed = _parse_date(date_str)
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    return None

