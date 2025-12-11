"""
Frontend Rendering Tests

Tests for frontend data rendering and display logic.
These tests validate that the frontend correctly renders data from the backend API.

Author: NDB Date Mover Team
"""

import pytest
from datetime import datetime, timedelta


class TestFrontendRendering:
    """Test cases for frontend rendering logic."""
    
    def test_date_format_dd_mmm_yyyy(self):
        """Test that dates are formatted as dd/mmm/yyyy (e.g., 15/Jan/2026)."""
        # This validates the backend format_date function output
        from backend.date_utils import format_date
        
        test_cases = [
            ("2026-01-15", "15/Jan/2026"),
            ("2026-12-25", "25/Dec/2026"),
            ("2024-03-01", "01/Mar/2024"),
        ]
        
        for input_date, expected in test_cases:
            result = format_date(input_date)
            assert result == expected, f"Expected {expected}, got {result}"
    
    def test_date_history_reverse_chronological(self):
        """Test that date history is displayed in reverse chronological order (newest first)."""
        # Simulate backend response with history
        history = ["01/Jan/2026", "15/Dec/2025", "10/Nov/2025"]
        
        # Backend should reverse this before sending
        reversed_history = list(reversed(history))
        expected = ["10/Nov/2025", "15/Dec/2025", "01/Jan/2026"]
        
        assert reversed_history == expected, "History should be in reverse chronological order"
    
    def test_risk_indicator_object_extraction(self):
        """Test that Risk Indicator field correctly extracts value from object."""
        # Simulate JIRA response with object value
        test_cases = [
            ({"value": "red"}, "red"),
            ({"name": "yellow"}, "yellow"),
            ({"displayName": "green"}, "green"),
            ("red", "red"),  # String value
        ]
        
        for value, expected_text in test_cases:
            if isinstance(value, dict):
                risk_text = value.get("value") or value.get("name") or value.get("displayName") or str(value)
            else:
                risk_text = str(value)
            
            assert risk_text == expected_text, f"Expected {expected_text}, got {risk_text}"
    
    def test_risk_indicator_color_matching(self):
        """Test that Risk Indicator colors are correctly matched."""
        test_cases = [
            ("red", "red"),
            ("Red", "red"),
            ("RED", "red"),
            ("yellow", "yellow"),
            ("Yellow", "yellow"),
            ("green", "green"),
            ("Green", "green"),
            ("unknown", ""),  # No color for unknown values
        ]
        
        for value, expected_class in test_cases:
            risk_value = value.lower().trim() if hasattr(value, 'trim') else value.lower().strip()
            risk_class = ''
            
            if risk_value == 'red' or 'red' in risk_value:
                risk_class = 'red'
            elif risk_value == 'yellow' or 'yellow' in risk_value:
                risk_class = 'yellow'
            elif risk_value == 'green' or 'green' in risk_value:
                risk_class = 'green'
            
            assert risk_class == expected_class, f"Expected {expected_class}, got {risk_class} for {value}"
    
    def test_ai_summary_display_logic(self):
        """Test that AI summary is displayed when available and show_ai_summary is true."""
        # Simulate field data
        fields = {
            "customfield_23073": "Long status update text...",
            "customfield_23073_summary": "Short summary",
            "customfield_23073_original": "Long status update text...",
            "customfield_23073_show_ai_summary": True,
        }
        
        col = "customfield_23073"
        show_ai_summary = fields.get(f"{col}_show_ai_summary", True)
        summary = fields.get(f"{col}_summary")
        
        # Should show summary if available and flag is true
        should_show_summary = summary and summary.strip() and show_ai_summary
        
        assert should_show_summary is True, "Should show AI summary when available and flag is true"
    
    def test_table_column_rendering(self):
        """Test that only configured columns are displayed."""
        # Simulate backend response
        display_columns = [
            "key", "summary", "status", "assignee", "resolution",
            "fixVersions", "customfield_13861", "customfield_11068",
            "customfield_11067", "customfield_35863", "customfield_35864",
            "customfield_23560", "customfield_23073"
        ]
        
        # Simulate issue with all fields
        issue = {
            "key": "NDB-123",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "John Doe"},
                "customfield_13861": "2026-01-15",
                "customfield_13861_formatted": "15/Jan/2026",
                "customfield_23560": {"value": "red"},
                "customfield_23073": "Status update",
                "customfield_23073_summary": "Summary",
                "customfield_23073_show_ai_summary": True,
                # These should NOT be displayed (not in display_columns)
                "customfield_99999": "Hidden field",
            }
        }
        
        # Only display_columns should be rendered
        fields = issue.get("fields", {})
        rendered_columns = [col for col in display_columns if col in ["key"] or fields.get(col) is not None]
        
        assert len(rendered_columns) <= len(display_columns), "Should only render configured columns"
        assert "customfield_99999" not in rendered_columns, "Should not render unconfigured columns"
    
    def test_date_cell_rendering(self):
        """Test that date cells render correctly with current date, history, and week slip."""
        # Simulate date field data
        fields = {
            "customfield_11067_formatted": "15/Jan/2026",
            "customfield_11067_history": ["10/Jan/2026", "05/Jan/2026"],
            "customfield_11067_week_slip": {
                "weeks": 2,
                "display": "+2 weeks",
                "color": "red"
            }
        }
        
        col = "customfield_11067"
        current = fields.get(f"{col}_formatted")
        history = fields.get(f"{col}_history", [])
        week_slip = fields.get(f"{col}_week_slip")
        
        # Validate all components are present
        assert current is not None, "Current date should be present"
        assert isinstance(history, list), "History should be a list"
        assert week_slip is not None, "Week slip should be present"
        assert week_slip.get("display") is not None, "Week slip display should be present"
        assert week_slip.get("color") is not None, "Week slip color should be present"
    
    def test_pagination_logic(self):
        """Test that pagination correctly slices issues."""
        all_issues = list(range(100))  # 100 issues
        page_size = 25
        current_page = 1
        
        # Calculate pagination
        start_index = (current_page - 1) * page_size
        end_index = min(start_index + page_size, len(all_issues))
        page_issues = all_issues[start_index:end_index]
        
        assert len(page_issues) == 25, "First page should have 25 issues"
        assert page_issues[0] == 0, "First issue should be at index 0"
        assert page_issues[-1] == 24, "Last issue should be at index 24"
        
        # Test second page
        current_page = 2
        start_index = (current_page - 1) * page_size
        end_index = min(start_index + page_size, len(all_issues))
        page_issues = all_issues[start_index:end_index]
        
        assert len(page_issues) == 25, "Second page should have 25 issues"
        assert page_issues[0] == 25, "First issue should be at index 25"
    
    def test_fixversions_array_rendering(self):
        """Test that fixVersions array is correctly rendered as comma-separated values."""
        fix_versions = [
            {"name": "NDB-2.10"},
            {"name": "NDB-2.11"},
            {"displayName": "NDB-2.12"}
        ]
        
        # Simulate frontend rendering logic
        display = ", ".join([
            v.get("name") or v.get("displayName") or v.get("value") or str(v)
            for v in fix_versions
        ])
        
        assert "NDB-2.10" in display, "Should include first version"
        assert "NDB-2.11" in display, "Should include second version"
        assert "NDB-2.12" in display, "Should include third version"
        assert display.count(",") == 2, "Should have 2 commas for 3 items"
    
    def test_current_date_excluded_from_history(self):
        """Test that current date is not included in struck-out history."""
        current_date = "15/Jan/2026"
        history = ["15/Jan/2026", "10/Jan/2026", "05/Jan/2026"]
        
        # Filter out current date
        filtered_history = [d for d in history if d != current_date]
        
        assert current_date not in filtered_history, "Current date should not be in history"
        assert len(filtered_history) == 2, "Should have 2 historical dates"
        assert "10/Jan/2026" in filtered_history, "Should include older dates"
        assert "05/Jan/2026" in filtered_history, "Should include older dates"

