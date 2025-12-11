"""
Unit tests for Date Display Module

Tests for date difference calculation and display formatting.

Author: NDB Date Mover Team
"""

import pytest
from backend.date_display import (
    calculate_date_difference_display,
    normalize_date_for_comparison,
    _calculate_weeks_with_rounding,
)


class TestCalculateDateDifferenceDisplay:
    """Test cases for date difference display calculation."""
    
    def test_less_than_7_days(self):
        """Test that differences < 7 days are shown as days."""
        result, unit = calculate_date_difference_display("2024-01-01", "2024-01-04")
        assert unit == "days"
        assert "3 days" in result
    
    def test_exactly_7_days(self):
        """Test that 7 days is shown as 1 week."""
        result, unit = calculate_date_difference_display("2024-01-01", "2024-01-08")
        assert unit == "weeks"
        assert "1 week" in result
    
    def test_8_days(self):
        """Test that 8 days is shown as 1 week."""
        result, unit = calculate_date_difference_display("2024-01-01", "2024-01-09")
        assert unit == "weeks"
        assert "1 week" in result
    
    def test_9_to_11_days(self):
        """Test that 9-11 days are shown as 1.5 weeks."""
        for days in [9, 10, 11]:
            result, unit = calculate_date_difference_display(
                "2024-01-01", 
                f"2024-01-{1+days:02d}"
            )
            assert unit == "weeks"
            assert "1.5 weeks" in result
    
    def test_12_days(self):
        """Test that 12 days is shown as 1.5 weeks."""
        result, unit = calculate_date_difference_display("2024-01-01", "2024-01-13")
        assert unit == "weeks"
        assert "1.5 weeks" in result
    
    def test_13_to_14_days(self):
        """Test that 13-14 days are shown as 2 weeks."""
        for days in [13, 14]:
            result, unit = calculate_date_difference_display(
                "2024-01-01",
                f"2024-01-{1+days:02d}"
            )
            assert unit == "weeks"
            assert "2 weeks" in result
    
    def test_15_days(self):
        """Test that 15 days is shown as 2 weeks."""
        result, unit = calculate_date_difference_display("2024-01-01", "2024-01-16")
        assert unit == "weeks"
        assert "2 weeks" in result
    
    def test_16_to_19_days(self):
        """Test that 16-19 days are shown as 2.5 weeks."""
        for days in [16, 17, 18, 19]:
            result, unit = calculate_date_difference_display(
                "2024-01-01",
                f"2024-01-{1+days:02d}"
            )
            assert unit == "weeks"
            assert "2.5 weeks" in result
    
    def test_20_to_22_days(self):
        """Test that 20-22 days are shown as 3 weeks."""
        for days in [20, 21, 22]:
            result, unit = calculate_date_difference_display(
                "2024-01-01",
                f"2024-01-{1+days:02d}"
            )
            assert unit == "weeks"
            assert "3 weeks" in result
    
    def test_23_to_26_days(self):
        """Test that 23-26 days are shown as 3.5 weeks."""
        for days in [23, 24, 25, 26]:
            result, unit = calculate_date_difference_display(
                "2024-01-01",
                f"2024-01-{1+days:02d}"
            )
            assert unit == "weeks"
            assert "3.5 weeks" in result
    
    def test_27_to_29_days(self):
        """Test that 27-29 days are shown as 4 weeks."""
        for days in [27, 28, 29]:
            result, unit = calculate_date_difference_display(
                "2024-01-01",
                f"2024-01-{1+days:02d}"
            )
            assert unit == "weeks"
            assert "4 weeks" in result
    
    def test_negative_difference(self):
        """Test that negative differences (ahead of schedule) work correctly."""
        result, unit = calculate_date_difference_display("2024-01-10", "2024-01-05")
        assert "-" in result
        assert unit == "days" or unit == "weeks"
    
    def test_zero_difference(self):
        """Test that zero difference is shown as 0 days."""
        result, unit = calculate_date_difference_display("2024-01-01", "2024-01-01")
        assert "0 days" in result
        assert unit == "days"
    
    def test_invalid_dates(self):
        """Test handling of invalid dates."""
        result, unit = calculate_date_difference_display("invalid", "2024-01-01")
        assert result == "N/A"
        assert unit == "unknown"


class TestNormalizeDateForComparison:
    """Test cases for date normalization."""
    
    def test_iso_format(self):
        """Test normalization of ISO format dates."""
        result = normalize_date_for_comparison("2024-01-15")
        assert result == "2024-01-15"
    
    def test_iso_with_time(self):
        """Test normalization of ISO format with time."""
        result = normalize_date_for_comparison("2024-01-15T10:30:00")
        assert result == "2024-01-15"
    
    def test_mmddyyyy_format(self):
        """Test normalization of MM/DD/YYYY format."""
        result = normalize_date_for_comparison("01/15/2024")
        assert result == "2024-01-15"
    
    def test_ddmmyyyy_format(self):
        """Test normalization of DD/MM/YYYY format."""
        result = normalize_date_for_comparison("15/01/2024")
        assert result == "2024-01-15"
    
    def test_invalid_date(self):
        """Test handling of invalid date."""
        result = normalize_date_for_comparison("invalid")
        assert result is None
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = normalize_date_for_comparison("")
        assert result is None


class TestCalculateWeeksWithRounding:
    """Test cases for weeks calculation with rounding."""
    
    def test_7_days(self):
        """Test 7 days = 1 week."""
        assert _calculate_weeks_with_rounding(7) == 1.0
    
    def test_8_days(self):
        """Test 8 days = 1 week."""
        assert _calculate_weeks_with_rounding(8) == 1.0
    
    def test_9_to_11_days(self):
        """Test 9-11 days = 1.5 weeks."""
        for days in [9, 10, 11]:
            assert _calculate_weeks_with_rounding(days) == 1.5
    
    def test_12_days(self):
        """Test 12 days = 1.5 weeks."""
        assert _calculate_weeks_with_rounding(12) == 1.5
    
    def test_13_to_14_days(self):
        """Test 13-14 days = 2 weeks."""
        for days in [13, 14]:
            assert _calculate_weeks_with_rounding(days) == 2.0
    
    def test_15_days(self):
        """Test 15 days = 2 weeks."""
        assert _calculate_weeks_with_rounding(15) == 2.0
    
    def test_16_to_19_days(self):
        """Test 16-19 days = 2.5 weeks."""
        for days in [16, 17, 18, 19]:
            assert _calculate_weeks_with_rounding(days) == 2.5
    
    def test_20_to_22_days(self):
        """Test 20-22 days = 3 weeks."""
        for days in [20, 21, 22]:
            assert _calculate_weeks_with_rounding(days) == 3.0
    
    def test_23_to_26_days(self):
        """Test 23-26 days = 3.5 weeks."""
        for days in [23, 24, 25, 26]:
            assert _calculate_weeks_with_rounding(days) == 3.5
    
    def test_27_to_29_days(self):
        """Test 27-29 days = 4 weeks."""
        for days in [27, 28, 29]:
            assert _calculate_weeks_with_rounding(days) == 4.0
    
    def test_30_to_33_days(self):
        """Test 30-33 days = 4.5 weeks."""
        for days in [30, 31, 32, 33]:
            assert _calculate_weeks_with_rounding(days) == 4.5
    
    def test_larger_values(self):
        """Test that larger values follow the same pattern."""
        # 34-36 days = 5 weeks
        for days in [34, 35, 36]:
            assert _calculate_weeks_with_rounding(days) == 5.0
        # 37-40 days = 5.5 weeks
        for days in [37, 38, 39, 40]:
            assert _calculate_weeks_with_rounding(days) == 5.5

