"""
Unit tests for Date Utility Functions

Author: NDB Date Mover Team
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime

from backend.date_utils import (
    format_date,
    calculate_week_slip,
    parse_date,
    extract_date_history,
    get_week_slip_color,
)


class TestDateFormatting:
    """Test cases for date formatting."""

    def test_format_iso_date(self):
        """Test formatting ISO date to dd/mmm/yyyy."""
        result = format_date("2024-12-25T10:30:00.000+0000", "mm/dd/yyyy")
        assert result == "25/Dec/2024"

    def test_format_simple_date(self):
        """Test formatting simple date."""
        result = format_date("2024-12-25", "mm/dd/yyyy")
        assert result == "25/Dec/2024"

    def test_format_different_target(self):
        """Test formatting - always returns dd/mmm/yyyy regardless of target."""
        # Display format is always dd/mmm/yyyy, even if different target specified
        result = format_date("2024-12-25", "yyyy-mm-dd")
        assert result == "25/Dec/2024"  # Always dd/mmm/yyyy for display

    def test_format_invalid_date(self):
        """Test formatting invalid date returns original."""
        result = format_date("invalid-date", "mm/dd/yyyy")
        assert result == "invalid-date"

    def test_format_empty_date(self):
        """Test formatting empty date."""
        result = format_date("", "mm/dd/yyyy")
        assert result == ""


class TestWeekSlipCalculation:
    """Test cases for week slip calculation."""

    def test_positive_week_slip(self):
        """Test positive week slip (delay)."""
        weeks, week_str = calculate_week_slip("2024-01-01", "2024-01-22")
        assert weeks == 3
        assert "+3 weeks" in week_str

    def test_negative_week_slip(self):
        """Test negative week slip (ahead)."""
        weeks, week_str = calculate_week_slip("2024-01-22", "2024-01-01")
        assert weeks == -3
        assert "-3" in week_str

    def test_zero_week_slip(self):
        """Test zero week slip."""
        weeks, week_str = calculate_week_slip("2024-01-01", "2024-01-01")
        assert weeks == 0
        # For 0 delta, we display "0 days" (consistent with date difference display rules)
        assert "0 days" in week_str

    def test_partial_week(self):
        """Test partial week calculation."""
        weeks, week_str = calculate_week_slip("2024-01-01", "2024-01-05")
        # 4 days should round to 1 week or 0 weeks depending on rounding
        assert weeks in [0, 1]

    def test_invalid_dates(self):
        """Test with invalid dates."""
        weeks, week_str = calculate_week_slip("invalid", "2024-01-01")
        assert weeks == 0
        assert week_str == "N/A"


class TestDateParsing:
    """Test cases for date parsing."""

    def test_parse_iso_date(self):
        """Test parsing ISO date."""
        result = parse_date("2024-12-25T10:30:00.000+0000")
        assert result is not None
        assert isinstance(result, datetime)

    def test_parse_simple_date(self):
        """Test parsing simple date."""
        result = parse_date("2024-12-25")
        assert result is not None
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25

    def test_parse_invalid_date(self):
        """Test parsing invalid date."""
        result = parse_date("invalid")
        assert result is None


class TestDateHistoryExtraction:
    """Test cases for date history extraction."""

    def test_extract_date_history(self):
        """Test extracting date history from changelog."""
        changelog = [
            {
                "field": "customfield_12345",
                "field_name": "Target Date",
                "from": "2024-01-01",
                "to": "2024-01-15",
                "timestamp": "2024-01-10T10:00:00Z"
            },
            {
                "field": "customfield_12345",
                "field_name": "Target Date",
                "from": "2024-01-15",
                "to": "2024-01-22",
                "timestamp": "2024-01-20T10:00:00Z"
            },
            {
                "field": "customfield_67890",
                "field_name": "Other Field",
                "from": "old",
                "to": "new",
                "timestamp": "2024-01-15T10:00:00Z"
            }
        ]

        history = extract_date_history(changelog, "customfield_12345")
        assert len(history) == 2
        assert history[0][0] == "2024-01-15"  # First change
        assert history[1][0] == "2024-01-22"  # Second change

    def test_extract_no_history(self):
        """Test extracting history when none exists."""
        changelog = [
            {
                "field": "customfield_67890",
                "from": "old",
                "to": "new",
                "timestamp": "2024-01-15T10:00:00Z"
            }
        ]

        history = extract_date_history(changelog, "customfield_12345")
        assert len(history) == 0


class TestWeekSlipColor:
    """Test cases for week slip color coding."""

    def test_positive_slip_color(self):
        """Test color for positive slip (delay)."""
        assert get_week_slip_color(3) == "red"

    def test_negative_slip_color(self):
        """Test color for negative slip (ahead)."""
        assert get_week_slip_color(-2) == "green"

    def test_zero_slip_color(self):
        """Test color for zero slip."""
        assert get_week_slip_color(0) == "gray"

