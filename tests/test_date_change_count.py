"""
Tests for Date Change Count and Difference Calculation

Tests to ensure:
1. Change count includes all changes (including reverts: A->B->A = 3 changes)
2. Difference calculation from first date to current date works correctly

Author: NDB Date Mover Team
"""

import pytest
from backend.date_utils import extract_date_history, calculate_week_slip
from backend.date_display import calculate_date_difference_display


class TestChangeCount:
    """Test change count calculation."""
    
    def test_change_count_includes_reverts(self):
        """Test that change count includes reverts (A->B->A = 3 changes)."""
        # Simulate changelog with reverts
        changelog = [
            {"field": "customfield_12345", "to": "2025-01-01", "timestamp": "2025-01-01T10:00:00"},
            {"field": "customfield_12345", "to": "2025-01-15", "timestamp": "2025-01-15T10:00:00"},
            {"field": "customfield_12345", "to": "2025-01-01", "timestamp": "2025-01-20T10:00:00"},
        ]
        
        date_history = extract_date_history(changelog, "customfield_12345")
        change_count = len(date_history)
        
        assert change_count == 3, "Change count should be 3 (A->B->A)"
    
    def test_change_count_single_change(self):
        """Test change count with single change."""
        changelog = [
            {"field": "customfield_12345", "to": "2025-01-01", "timestamp": "2025-01-01T10:00:00"},
        ]
        
        date_history = extract_date_history(changelog, "customfield_12345")
        change_count = len(date_history)
        
        assert change_count == 1, "Change count should be 1"
    
    def test_change_count_multiple_changes(self):
        """Test change count with multiple changes."""
        changelog = [
            {"field": "customfield_12345", "to": "2025-01-01", "timestamp": "2025-01-01T10:00:00"},
            {"field": "customfield_12345", "to": "2025-01-15", "timestamp": "2025-01-15T10:00:00"},
            {"field": "customfield_12345", "to": "2025-02-01", "timestamp": "2025-02-01T10:00:00"},
            {"field": "customfield_12345", "to": "2025-02-15", "timestamp": "2025-02-15T10:00:00"},
        ]
        
        date_history = extract_date_history(changelog, "customfield_12345")
        change_count = len(date_history)
        
        assert change_count == 4, "Change count should be 4"
    
    def test_change_count_no_history(self):
        """Test change count with no history."""
        changelog = []
        
        date_history = extract_date_history(changelog, "customfield_12345")
        change_count = len(date_history)
        
        assert change_count == 0, "Change count should be 0"


class TestDateDifference:
    """Test date difference calculation from first date to current."""
    
    def test_difference_first_to_current_less_than_7_days(self):
        """Test difference calculation when < 7 days."""
        first_date = "2025-01-01"
        current_date = "2025-01-05"
        
        display_str, unit_type = calculate_date_difference_display(first_date, current_date)
        
        assert unit_type == "days", "Should be in days"
        assert "4 days" in display_str or "+4 days" in display_str, f"Expected '4 days', got '{display_str}'"
    
    def test_difference_first_to_current_exactly_7_days(self):
        """Test difference calculation when exactly 7 days."""
        first_date = "2025-01-01"
        current_date = "2025-01-08"
        
        display_str, unit_type = calculate_date_difference_display(first_date, current_date)
        
        assert unit_type == "weeks", "Should be in weeks"
        assert "1 week" in display_str or "+1 week" in display_str, f"Expected '1 week', got '{display_str}'"
    
    def test_difference_first_to_current_9_days(self):
        """Test difference calculation when 9 days (should be 1.5 weeks)."""
        first_date = "2025-01-01"
        current_date = "2025-01-10"
        
        display_str, unit_type = calculate_date_difference_display(first_date, current_date)
        
        assert unit_type == "weeks", "Should be in weeks"
        assert "1.5 weeks" in display_str or "+1.5 weeks" in display_str, f"Expected '1.5 weeks', got '{display_str}'"
    
    def test_difference_first_to_current_14_days(self):
        """Test difference calculation when 14 days (should be 2 weeks)."""
        first_date = "2025-01-01"
        current_date = "2025-01-15"
        
        display_str, unit_type = calculate_date_difference_display(first_date, current_date)
        
        assert unit_type == "weeks", "Should be in weeks"
        assert "2 weeks" in display_str or "+2 weeks" in display_str, f"Expected '2 weeks', got '{display_str}'"
    
    def test_difference_first_to_current_negative(self):
        """Test difference calculation when current is before first (ahead of schedule)."""
        first_date = "2025-01-15"
        current_date = "2025-01-01"
        
        display_str, unit_type = calculate_date_difference_display(first_date, current_date)
        
        # Should show negative difference (ahead of schedule)
        assert "-" in display_str or "ahead" in display_str.lower(), f"Expected negative/ahead indicator, got '{display_str}'"
    
    def test_difference_first_to_current_same_date(self):
        """Test difference calculation when first and current are the same."""
        first_date = "2025-01-01"
        current_date = "2025-01-01"
        
        display_str, unit_type = calculate_date_difference_display(first_date, current_date)
        
        assert "0 days" in display_str or "0" in display_str, f"Expected '0 days', got '{display_str}'"
    
    def test_week_slip_uses_first_date(self):
        """Test that week_slip calculation uses first date from history."""
        first_date = "2025-01-01"
        current_date = "2025-01-15"
        
        weeks, week_str = calculate_week_slip(first_date, current_date)
        
        assert weeks > 0, "Should be positive weeks"
        assert "week" in week_str.lower() or "days" in week_str.lower(), f"Expected week/days string, got '{week_str}'"

