"""
Unit tests for AI Summarizer Module

Tests for executive-friendly text summarization functionality.

Author: NDB Date Mover Team
"""

import pytest
from backend.ai_summarizer import summarize_for_executives, summarize_status_update


class TestSummarizeForExecutives:
    """Test cases for general executive summarization."""
    
    def test_short_text_no_change(self):
        """Test that short text is returned as-is."""
        text = "Project is on track."
        result = summarize_for_executives(text, max_length=200)
        assert result == text
    
    def test_long_text_truncated(self):
        """Test that long text is truncated to max_length."""
        text = "This is a very long status update " * 20  # ~600 chars
        result = summarize_for_executives(text, max_length=200)
        assert len(result) <= 200
        assert result.endswith('...')
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = summarize_for_executives("", max_length=200)
        assert result == ""
    
    def test_none_input(self):
        """Test handling of None input."""
        result = summarize_for_executives(None, max_length=200)
        assert result == ""
    
    def test_first_sentence_extraction(self):
        """Test that first sentence is extracted when possible."""
        text = "Project is on track. We have completed phase 1. Next steps include testing."
        result = summarize_for_executives(text, max_length=200)
        assert "Project is on track" in result
        assert result.endswith('.')
    
    def test_word_boundary_truncation(self):
        """Test that truncation happens at word boundaries."""
        text = "This is a test " * 30  # Long text
        result = summarize_for_executives(text, max_length=50)
        # Should end at word boundary, not mid-word
        assert not result[-4:-1].endswith(' ')


class TestSummarizeStatusUpdate:
    """Test cases for status update summarization."""
    
    def test_basic_summarization(self):
        """Test basic status update summarization."""
        text = "Status: We have made significant progress this week. The team completed all planned tasks."
        result = summarize_status_update(text)
        assert len(result) <= 200
        assert "Status:" not in result  # Prefix should be removed
    
    def test_prefix_removal(self):
        """Test that common prefixes are removed."""
        prefixes = ["Status:", "Update:", "Note:", "Comment:"]
        for prefix in prefixes:
            text = f"{prefix} This is the actual content."
            result = summarize_status_update(text)
            assert not result.startswith(prefix)
            assert "This is the actual content" in result
    
    def test_empty_status(self):
        """Test handling of empty status update."""
        result = summarize_status_update("")
        assert result == ""
    
    def test_long_status_summarized(self):
        """Test that long status updates are summarized."""
        text = "This is a very detailed status update. " * 20
        result = summarize_status_update(text)
        assert len(result) <= 200
    
    def test_status_with_html(self):
        """Test handling of status with HTML-like content."""
        text = "<p>Status update with HTML tags</p>"
        result = summarize_status_update(text)
        assert len(result) > 0

