"""
Tests for Date Comparison Fix

Tests to ensure current date is properly excluded from history,
even when dates are in different formats (e.g., 13/Jun/2025 vs 13/Jun/25).

Author: NDB Date Mover Team
"""

import pytest
from backend.date_display import normalize_date_for_comparison, _parse_date
from backend.date_utils import format_date, parse_date


class TestDateParsing:
    """Test date parsing with dd/mmm/yyyy format support."""
    
    def test_parse_dd_mmm_yyyy_format(self):
        """Test parsing dd/mmm/yyyy format (e.g., 13/Jun/2025)."""
        result = _parse_date("13/Jun/2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 13
    
    def test_parse_dd_mmm_yy_format(self):
        """Test parsing dd/mmm/yy format (e.g., 13/Jun/25)."""
        result = _parse_date("13/Jun/25")
        assert result is not None
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 13
    
    def test_parse_iso_format(self):
        """Test parsing ISO format (e.g., 2025-06-13)."""
        result = _parse_date("2025-06-13")
        assert result is not None
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 13
    
    def test_parse_iso_with_time(self):
        """Test parsing ISO format with time."""
        result = _parse_date("2025-06-13T10:30:00")
        assert result is not None
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 13


class TestDateNormalization:
    """Test date normalization for comparison."""
    
    def test_normalize_dd_mmm_yyyy(self):
        """Test normalization of dd/mmm/yyyy format."""
        result = normalize_date_for_comparison("13/Jun/2025")
        assert result == "2025-06-13"
    
    def test_normalize_dd_mmm_yy(self):
        """Test normalization of dd/mmm/yy format."""
        result = normalize_date_for_comparison("13/Jun/25")
        assert result == "2025-06-13"
    
    def test_normalize_iso_format(self):
        """Test normalization of ISO format."""
        result = normalize_date_for_comparison("2025-06-13")
        assert result == "2025-06-13"
    
    def test_normalize_iso_with_time(self):
        """Test normalization of ISO format with time."""
        result = normalize_date_for_comparison("2025-06-13T10:30:00")
        assert result == "2025-06-13"
    
    def test_normalize_same_date_different_formats(self):
        """Test that same date in different formats normalizes to same value."""
        formats = [
            "2025-06-13",
            "2025-06-13T10:30:00",
            "13/Jun/2025",
            "13/Jun/25",
        ]
        
        normalized = [normalize_date_for_comparison(f) for f in formats]
        # All should normalize to the same value
        assert all(n == "2025-06-13" for n in normalized if n)


class TestCurrentDateExclusion:
    """Test that current date is excluded from history."""
    
    def test_exclude_current_date_same_format(self):
        """Test exclusion when current and history are in same format."""
        current = "2025-06-13"
        history = "2025-06-13"
        
        current_norm = normalize_date_for_comparison(current)
        history_norm = normalize_date_for_comparison(history)
        
        should_exclude = current_norm == history_norm
        assert should_exclude is True
    
    def test_exclude_current_date_different_formats(self):
        """Test exclusion when current and history are in different formats."""
        # Current from JIRA (ISO)
        current = "2025-06-13"
        # History might be in formatted string
        history = "13/Jun/2025"
        
        current_norm = normalize_date_for_comparison(current)
        history_norm = normalize_date_for_comparison(history)
        
        should_exclude = current_norm == history_norm
        assert should_exclude is True
    
    def test_exclude_current_date_short_year(self):
        """Test exclusion when history has short year format."""
        current = "2025-06-13"
        history = "13/Jun/25"  # Short year
        
        current_norm = normalize_date_for_comparison(current)
        history_norm = normalize_date_for_comparison(history)
        
        should_exclude = current_norm == history_norm
        assert should_exclude is True
    
    def test_include_different_dates(self):
        """Test that different dates are NOT excluded."""
        current = "2025-06-13"
        history = "2025-06-14"  # Different date
        
        current_norm = normalize_date_for_comparison(current)
        history_norm = normalize_date_for_comparison(history)
        
        should_exclude = current_norm == history_norm
        assert should_exclude is False
    
    def test_format_date_handles_already_formatted(self):
        """Test that format_date can handle already-formatted dates."""
        # If a date is already in dd/mmm/yyyy format, format_date should still work
        result = format_date("13/Jun/2025")
        assert result == "13/Jun/2025"  # Should format correctly
    
    def test_format_date_handles_iso(self):
        """Test that format_date handles ISO format."""
        result = format_date("2025-06-13")
        assert result == "13/Jun/2025"
    
    def test_comparison_with_formatted_dates(self):
        """Test comparison when both dates are already formatted."""
        current_formatted = "13/Jun/2025"
        history_formatted = "13/Jun/25"
        
        # Normalize formatted dates
        current_norm = normalize_date_for_comparison(current_formatted)
        history_norm = normalize_date_for_comparison(history_formatted)
        
        should_exclude = current_norm == history_norm
        assert should_exclude is True, "Same date in different formatted formats should match"

