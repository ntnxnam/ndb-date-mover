"""
Test Suite for Story Points Calculator

Tests story points calculation, Dev/QA grouping, work item filtering,
resolution categorization, hyperlinks, and total calculations.

Comprehensive coverage including:
- Functional tests
- NFR (Non-Functional Requirements) tests
- Corner cases
- Negative cases
- Edge cases

Author: NDB Date Mover Team
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from backend.story_points_calculator import (
    is_work_item,
    categorize_issue_for_dev_qa,
    categorize_resolution,
    get_story_points,
    calculate_story_points_breakdown,
    format_story_points_breakdown,
    build_related_tickets_jql,
    build_jql_for_category,
    NON_WORK_ITEM_TYPES,
    DEFAULT_POSITIVE_RESOLUTIONS,
)


class TestWorkItemFiltering(unittest.TestCase):
    """Test work item filtering logic"""

    def test_is_work_item_task(self):
        """Test that Task is a work item"""
        self.assertTrue(is_work_item("Task"))

    def test_is_work_item_bug(self):
        """Test that Bug is a work item"""
        self.assertTrue(is_work_item("Bug"))

    def test_is_work_item_test(self):
        """Test that Test is a work item"""
        self.assertTrue(is_work_item("Test"))

    def test_is_work_item_test_plan(self):
        """Test that Test Plan is a work item"""
        self.assertTrue(is_work_item("Test Plan"))

    def test_is_work_item_devdocs(self):
        """Test that DevDocs is a work item"""
        self.assertTrue(is_work_item("DevDocs"))

    def test_is_not_work_item_epic(self):
        """Test that Epic is NOT a work item"""
        self.assertFalse(is_work_item("Epic"))

    def test_is_not_work_item_feature(self):
        """Test that Feature is NOT a work item"""
        self.assertFalse(is_work_item("Feature"))

    def test_is_not_work_item_initiative(self):
        """Test that Initiative is NOT a work item"""
        self.assertFalse(is_work_item("Initiative"))

    def test_is_not_work_item_xfeat(self):
        """Test that X-FEAT is NOT a work item"""
        self.assertFalse(is_work_item("X-FEAT"))

    def test_is_not_work_item_capability(self):
        """Test that Capability is NOT a work item"""
        self.assertFalse(is_work_item("Capability"))

    def test_is_work_item_case_insensitive(self):
        """Test that filtering is case insensitive"""
        self.assertFalse(is_work_item("EPIC"))
        self.assertFalse(is_work_item("epic"))
        self.assertFalse(is_work_item("EpIc"))
        self.assertTrue(is_work_item("TASK"))
        self.assertTrue(is_work_item("task"))

    def test_is_work_item_none(self):
        """Test that None/empty defaults to work item"""
        self.assertTrue(is_work_item(None))
        self.assertTrue(is_work_item(""))

    def test_is_work_item_partial_matches(self):
        """Test that partial matches in issue type names are handled"""
        # Should match "epic" anywhere in the name
        self.assertFalse(is_work_item("Epic Story"))
        self.assertFalse(is_work_item("Feature Request"))
        self.assertFalse(is_work_item("Initiative Plan"))
        self.assertTrue(is_work_item("Task Item"))
        self.assertTrue(is_work_item("Bug Report"))

    def test_is_work_item_all_non_work_types(self):
        """Test all non-work item types are excluded"""
        non_work_types = ["Epic", "Feature", "Initiative", "X-FEAT", "Capability",
                         "epic", "feature", "initiative", "x-feat", "capability"]
        for issue_type in non_work_types:
            self.assertFalse(is_work_item(issue_type), 
                           f"{issue_type} should NOT be a work item")

    def test_is_work_item_all_work_types(self):
        """Test common work item types are included"""
        work_types = ["Task", "Bug", "Test", "Test Plan", "DevDocs", "Story", 
                     "Subtask", "Improvement", "Technical Debt"]
        for issue_type in work_types:
            self.assertTrue(is_work_item(issue_type), 
                          f"{issue_type} should be a work item")


class TestDevQACategorization(unittest.TestCase):
    """Test Dev/QA categorization logic"""

    def test_categorize_test_as_qa(self):
        """Test that Test issue type is categorized as QA"""
        self.assertEqual(categorize_issue_for_dev_qa("Test"), "QA")

    def test_categorize_test_plan_as_qa(self):
        """Test that Test Plan issue type is categorized as QA"""
        self.assertEqual(categorize_issue_for_dev_qa("Test Plan"), "QA")

    def test_categorize_task_as_dev(self):
        """Test that Task issue type is categorized as Dev"""
        self.assertEqual(categorize_issue_for_dev_qa("Task"), "Dev")

    def test_categorize_bug_as_dev(self):
        """Test that Bug issue type is categorized as Dev"""
        self.assertEqual(categorize_issue_for_dev_qa("Bug"), "Dev")

    def test_categorize_improvement_as_dev(self):
        """Test that Improvement issue type is categorized as Dev"""
        self.assertEqual(categorize_issue_for_dev_qa("Improvement"), "Dev")

    def test_categorize_case_insensitive(self):
        """Test that categorization is case insensitive"""
        self.assertEqual(categorize_issue_for_dev_qa("TEST"), "QA")
        self.assertEqual(categorize_issue_for_dev_qa("test"), "QA")
        self.assertEqual(categorize_issue_for_dev_qa("TASK"), "Dev")

    def test_categorize_none_defaults_to_dev(self):
        """Test that None/empty defaults to Dev"""
        self.assertEqual(categorize_issue_for_dev_qa(None), "Dev")
        self.assertEqual(categorize_issue_for_dev_qa(""), "Dev")

    def test_categorize_test_plan_variations(self):
        """Test various Test Plan naming variations"""
        self.assertEqual(categorize_issue_for_dev_qa("Test Plan"), "QA")
        self.assertEqual(categorize_issue_for_dev_qa("test plan"), "QA")
        self.assertEqual(categorize_issue_for_dev_qa("TEST PLAN"), "QA")
        self.assertEqual(categorize_issue_for_dev_qa("TestPlan"), "QA")

    def test_categorize_test_variations(self):
        """Test various Test naming variations"""
        self.assertEqual(categorize_issue_for_dev_qa("Test"), "QA")
        self.assertEqual(categorize_issue_for_dev_qa("test"), "QA")
        self.assertEqual(categorize_issue_for_dev_qa("TEST"), "QA")

    def test_categorize_non_test_issue_types(self):
        """Test that non-test issue types are categorized as Dev"""
        dev_types = ["Task", "Bug", "Story", "Improvement", "Subtask", "DevDocs"]
        for issue_type in dev_types:
            self.assertEqual(categorize_issue_for_dev_qa(issue_type), "Dev", 
                           f"{issue_type} should be Dev")


class TestResolutionCategorization(unittest.TestCase):
    """Test resolution categorization logic"""

    def test_positive_resolution_fixed(self):
        """Test that Fixed is a positive resolution"""
        self.assertEqual(categorize_resolution("Fixed"), "positive")

    def test_positive_resolution_done(self):
        """Test that Done is a positive resolution"""
        self.assertEqual(categorize_resolution("Done"), "positive")

    def test_positive_resolution_resolved(self):
        """Test that Resolved is a positive resolution"""
        self.assertEqual(categorize_resolution("Resolved"), "positive")

    def test_positive_resolution_complete(self):
        """Test that Complete is a positive resolution"""
        self.assertEqual(categorize_resolution("Complete"), "positive")

    def test_negative_resolution_wont_do(self):
        """Test that Won't Do is a negative resolution"""
        self.assertEqual(categorize_resolution("Won't Do"), "negative")

    def test_negative_resolution_duplicate(self):
        """Test that Duplicate is a negative resolution"""
        self.assertEqual(categorize_resolution("Duplicate"), "negative")

    def test_unresolved_none(self):
        """Test that None resolution is unresolved"""
        self.assertEqual(categorize_resolution(None), "unresolved")

    def test_unresolved_empty(self):
        """Test that empty resolution is unresolved"""
        self.assertEqual(categorize_resolution(""), "unresolved")

    def test_custom_positive_resolutions(self):
        """Test custom positive resolutions"""
        custom_positive = {"CustomPositive", "AnotherPositive"}
        self.assertEqual(
            categorize_resolution("CustomPositive", custom_positive), "positive"
        )
        self.assertEqual(
            categorize_resolution("AnotherPositive", custom_positive), "positive"
        )
        self.assertEqual(
            categorize_resolution("NotInList", custom_positive), "negative"
        )

    def test_resolution_case_insensitive(self):
        """Test that resolution categorization is case insensitive"""
        self.assertEqual(categorize_resolution("FIXED"), "positive")
        self.assertEqual(categorize_resolution("fixed"), "positive")
        self.assertEqual(categorize_resolution("Fixed"), "positive")
        self.assertEqual(categorize_resolution("DONE"), "positive")
        self.assertEqual(categorize_resolution("done"), "positive")

    def test_resolution_whitespace_handling(self):
        """Test handling of resolutions with whitespace"""
        self.assertEqual(categorize_resolution("Won't Do"), "negative")
        # Note: Exact match required, so spaces matter unless normalized

    def test_resolution_all_positive_types(self):
        """Test all default positive resolution types"""
        positive_resolutions = DEFAULT_POSITIVE_RESOLUTIONS
        for res in positive_resolutions:
            self.assertEqual(categorize_resolution(res, positive_resolutions), "positive",
                           f"{res} should be positive")

    def test_resolution_negative_examples(self):
        """Test various negative resolution examples"""
        negative_resolutions = ["Won't Do", "Won't Fix", "Duplicate", "Cannot Reproduce", 
                               "Incomplete", "Rejected", "Cancelled", "Invalid"]
        for res in negative_resolutions:
            result = categorize_resolution(res)
            self.assertIn(result, ["negative", "unresolved"], 
                         f"{res} should be negative or unresolved")

    def test_resolution_empty_string(self):
        """Test that empty string is treated as unresolved"""
        self.assertEqual(categorize_resolution(""), "unresolved")


class TestStoryPointsExtraction(unittest.TestCase):
    """Test story points extraction from issues"""

    def test_get_story_points_from_customfield_10002(self):
        """Test extracting story points from customfield_10002"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": 5.0}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 5.0)

    def test_get_story_points_from_config_field(self):
        """Test extracting story points using configured field ID"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": 8.0}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 8.0)

    def test_get_story_points_zero(self):
        """Test that zero story points returns 0.0"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": 0}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 0.0)

    def test_get_story_points_none(self):
        """Test that missing story points returns 0.0"""
        issue = {
            "key": "TEST-123",
            "fields": {}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 0.0)

    def test_get_story_points_integer(self):
        """Test that integer story points are converted to float"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": 3}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 3.0)
        self.assertIsInstance(result, float)

    def test_get_story_points_fallback(self):
        """Test fallback to other story points fields"""
        issue = {
            "key": "TEST-123",
            "fields": {
                "customfield_10002": None,
                "customfield_10016": 7.0
            }
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 7.0)

    def test_get_story_points_string_value(self):
        """Test handling of string story points value"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": "5.5"}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 5.5)

    def test_get_story_points_negative_value(self):
        """Test handling of negative story points (edge case)"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": -5.0}
        }
        result = get_story_points(issue, "customfield_10002")
        # Should return the value as-is (even if negative)
        self.assertEqual(result, -5.0)

    def test_get_story_points_very_large_value(self):
        """Test handling of very large story points value"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": 999999.99}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 999999.99)

    def test_get_story_points_empty_string(self):
        """Test handling of empty string story points"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": ""}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 0.0)

    def test_get_story_points_none_value(self):
        """Test handling of None story points value"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10002": None}
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 0.0)

    def test_get_story_points_missing_fields_key(self):
        """Test handling when fields key is missing"""
        issue = {
            "key": "TEST-123"
            # No "fields" key
        }
        result = get_story_points(issue, "customfield_10002")
        self.assertEqual(result, 0.0)

    def test_get_story_points_none_field_id(self):
        """Test story points extraction when field ID is None"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10016": 5.0}
        }
        result = get_story_points(issue, None)
        # Should fallback to common field IDs
        self.assertEqual(result, 5.0)


class TestJQLQueryBuilder(unittest.TestCase):
    """Test JQL query building for related tickets"""

    def test_build_jql_single_key(self):
        """Test building JQL for a single issue key"""
        keys = ["ERA-48896"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("ERA-48896", jql)
        self.assertIn("key IN", jql)

    def test_build_jql_multiple_keys(self):
        """Test building JQL for multiple issue keys"""
        keys = ["ERA-48896", "ERA-44920"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("ERA-48896", jql)
        self.assertIn("ERA-44920", jql)

    def test_build_jql_empty_list(self):
        """Test building JQL with empty list"""
        keys = []
        jql = build_related_tickets_jql(keys)
        self.assertEqual(jql, "")

    def test_build_jql_includes_parent_link(self):
        """Test that JQL includes Parent Link field"""
        keys = ["ERA-48896"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("Parent Link", jql)

    def test_build_jql_includes_portfolio_children(self):
        """Test that JQL includes portfolio children"""
        keys = ["ERA-48896"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("portfolioChildrenOf", jql)

    def test_build_jql_includes_subtasks(self):
        """Test that JQL includes subtasks"""
        keys = ["ERA-48896"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("subtasksOf", jql)

    def test_build_jql_includes_epics(self):
        """Test that JQL includes issues in epics"""
        keys = ["ERA-48896"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("issuesInEpics", jql)

    def test_build_jql_includes_feat_fields(self):
        """Test that JQL includes FEAT ID and FEAT Number"""
        keys = ["ERA-48896"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("FEAT ID", jql)
        self.assertIn("FEAT Number", jql)

    def test_build_jql_complex_structure(self):
        """Test that JQL has proper OR structure"""
        keys = ["ERA-48896", "ERA-44920"]
        jql = build_related_tickets_jql(keys)
        # Should have multiple OR clauses
        or_count = jql.count(" OR ")
        self.assertGreater(or_count, 0)

    def test_build_jql_special_characters(self):
        """Test JQL building with special characters in keys"""
        keys = ["TEST-123", "TEST-456"]
        jql = build_related_tickets_jql(keys)
        # Should handle special characters correctly
        self.assertIn("TEST-123", jql)
        self.assertIn("TEST-456", jql)

    def test_build_jql_single_character_key(self):
        """Test JQL building with single character issue key"""
        keys = ["A"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("A", jql)

    def test_build_jql_very_long_key(self):
        """Test JQL building with very long issue key"""
        keys = ["VERY-LONG-PROJECT-KEY-123456789"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("VERY-LONG-PROJECT-KEY-123456789", jql)


class TestJQLCategoryBuilder(unittest.TestCase):
    """Test JQL query building for specific categories"""

    def test_build_jql_positive_dev(self):
        """Test building JQL for positive Dev category"""
        issue_keys = ["ERA-48896"]
        jql = build_jql_for_category(issue_keys, "positive", "Dev", {"Fixed", "Done"})
        self.assertIn("ERA-48896", jql)
        self.assertIn("resolution IN", jql)
        self.assertIn("Fixed", jql)
        self.assertIn("NOT IN (\"Test\", \"Test Plan\")", jql)
        self.assertIn("NOT IN (\"Epic\", \"Feature\"", jql)

    def test_build_jql_negative_qa(self):
        """Test building JQL for negative QA category"""
        issue_keys = ["ERA-48896"]
        jql = build_jql_for_category(issue_keys, "negative", "QA", {"Fixed", "Done"})
        self.assertIn("ERA-48896", jql)
        self.assertIn("resolution IS NOT EMPTY", jql)
        self.assertIn("resolution NOT IN", jql)
        self.assertIn("issuetype IN (\"Test\", \"Test Plan\")", jql)

    def test_build_jql_unresolved_dev(self):
        """Test building JQL for unresolved Dev category"""
        issue_keys = ["ERA-48896"]
        jql = build_jql_for_category(issue_keys, "unresolved", "Dev", {"Fixed", "Done"})
        self.assertIn("ERA-48896", jql)
        self.assertIn("resolution IS EMPTY", jql)
        self.assertIn("NOT IN (\"Test\", \"Test Plan\")", jql)

    def test_build_jql_multiple_keys(self):
        """Test building JQL with multiple issue keys"""
        issue_keys = ["ERA-48896", "ERA-44920"]
        jql = build_jql_for_category(issue_keys, "positive", "Dev", {"Fixed"})
        self.assertIn("ERA-48896", jql)
        self.assertIn("ERA-44920", jql)

    def test_build_jql_custom_positive_resolutions(self):
        """Test building JQL with custom positive resolutions"""
        issue_keys = ["ERA-48896"]
        custom_positive = {"CustomResolved", "CustomDone"}
        jql = build_jql_for_category(issue_keys, "positive", "Dev", custom_positive)
        self.assertIn("CustomResolved", jql)
        self.assertIn("CustomDone", jql)

    def test_build_jql_empty_issue_keys(self):
        """Test building JQL with empty issue keys"""
        issue_keys = []
        jql = build_jql_for_category(issue_keys, "positive", "Dev", {"Fixed"})
        # Should still build valid JQL (though may be empty base)
        self.assertIsInstance(jql, str)


class TestStoryPointsBreakdown(unittest.TestCase):
    """Test story points breakdown calculation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.mock_client.execute_jql = Mock(return_value={
            "success": True,
            "issues": []
        })

    def test_calculate_breakdown_empty_issue_keys(self):
        """Test breakdown with empty issue keys"""
        result = calculate_story_points_breakdown(
            self.mock_client, [], max_results=1000
        )
        self.assertEqual(result["positive"]["Dev"], 0.0)
        self.assertEqual(result["positive"]["QA"], 0.0)
        self.assertEqual(result["negative"]["Dev"], 0.0)
        self.assertEqual(result["negative"]["QA"], 0.0)
        self.assertEqual(result["unresolved"]["Dev"], 0.0)
        self.assertEqual(result["unresolved"]["QA"], 0.0)

    def test_calculate_breakdown_work_items_only(self):
        """Test that only work items are included"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TASK-101",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 5.0
                    }
                },
                {
                    "key": "EPIC-999",
                    "fields": {
                        "issuetype": {"name": "Epic"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 10.0
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TASK-101"], max_results=1000
        )
        # Only Task should be included, Epic should be excluded
        self.assertEqual(result["positive"]["Dev"], 5.0)
        self.assertEqual(result["positive"]["QA"], 0.0)

    def test_calculate_breakdown_dev_qa_grouping(self):
        """Test Dev/QA grouping"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "DEV-201",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 5.0
                    }
                },
                {
                    "key": "QA-301",
                    "fields": {
                        "issuetype": {"name": "Test"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 3.0
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["DEV-201"], max_results=1000
        )
        self.assertEqual(result["positive"]["Dev"], 5.0)
        self.assertEqual(result["positive"]["QA"], 3.0)

    def test_calculate_breakdown_resolution_categories(self):
        """Test resolution categorization"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "POS-401",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 5.0
                    }
                },
                {
                    "key": "NEG-501",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Won't Do"},
                        "customfield_10002": 3.0
                    }
                },
                {
                    "key": "OPEN-601",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": None,
                        "customfield_10002": 2.0
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["POS-401"], max_results=1000
        )
        self.assertEqual(result["positive"]["Dev"], 5.0)
        self.assertEqual(result["negative"]["Dev"], 3.0)
        self.assertEqual(result["unresolved"]["Dev"], 2.0)

    def test_calculate_breakdown_jql_query_failure(self):
        """Test handling of JQL query failure"""
        self.mock_client.execute_jql.return_value = {
            "success": False,
            "error": "JQL syntax error"
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        # Should return zero breakdown with error
        self.assertEqual(result["positive"]["Dev"], 0.0)
        self.assertEqual(result.get("error"), "JQL syntax error")

    def test_calculate_breakdown_no_story_points_field(self):
        """Test handling when story points field is missing"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"}
                        # No customfield_10002
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        # Should handle missing story points gracefully (0.0)
        self.assertEqual(result["positive"]["Dev"], 0.0)

    def test_calculate_breakdown_invalid_story_points_value(self):
        """Test handling of invalid story points values"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": "invalid"  # Not a number
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        # Should handle invalid values gracefully (0.0)
        self.assertEqual(result["positive"]["Dev"], 0.0)

    def test_calculate_breakdown_mixed_issue_types(self):
        """Test calculation with mixed issue types (work items and non-work items)"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 5.0
                    }
                },
                {
                    "key": "TEST-2",
                    "fields": {
                        "issuetype": {"name": "Epic"},  # Non-work item
                        "resolution": {"name": "Done"},
                        "customfield_10002": 10.0  # Should be excluded
                    }
                },
                {
                    "key": "TEST-3",
                    "fields": {
                        "issuetype": {"name": "Bug"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 3.0
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        # Only work items should be included (5.0 + 3.0 = 8.0)
        self.assertEqual(result["positive"]["Dev"], 8.0)

    def test_calculate_breakdown_all_resolution_types(self):
        """Test calculation with all resolution types"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {"key": "TEST-1", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Fixed"}, "customfield_10002": 5.0}},
                {"key": "TEST-2", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Done"}, "customfield_10002": 3.0}},
                {"key": "TEST-3", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Resolved"}, "customfield_10002": 2.0}},
                {"key": "TEST-4", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Complete"}, "customfield_10002": 1.0}},
                {"key": "TEST-5", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Won't Do"}, "customfield_10002": 4.0}},
                {"key": "TEST-6", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Duplicate"}, "customfield_10002": 6.0}},
                {"key": "TEST-7", "fields": {"issuetype": {"name": "Task"}, "resolution": None, "customfield_10002": 7.0}},
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        # Positive: 5 + 3 + 2 + 1 = 11
        self.assertEqual(result["positive"]["Dev"], 11.0)
        # Negative: 4 + 6 = 10
        self.assertEqual(result["negative"]["Dev"], 10.0)
        # Unresolved: 7
        self.assertEqual(result["unresolved"]["Dev"], 7.0)

    def test_calculate_breakdown_large_dataset(self):
        """Test calculation with large number of issues (performance test)"""
        issues = []
        for i in range(100):
            issues.append({
                "key": f"TEST-{i}",
                "fields": {
                    "issuetype": {"name": "Task" if i % 2 == 0 else "Test"},
                    "resolution": {"name": "Done" if i % 3 == 0 else None},
                    "customfield_10002": float(i % 10)
                }
            })
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": issues
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=2000
        )
        # Should handle large dataset without errors
        self.assertIn("positive", result)
        self.assertIn("negative", result)
        self.assertIn("unresolved", result)

    def test_calculate_breakdown_exception_handling(self):
        """Test exception handling during calculation"""
        self.mock_client.execute_jql.side_effect = Exception("Network error")
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        # Should return zero breakdown with error
        self.assertEqual(result["positive"]["Dev"], 0.0)
        self.assertIn("error", result)

    def test_calculate_breakdown_all_zeros(self):
        """Test calculation when all story points are zero"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 0.0
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        self.assertEqual(result["positive"]["Dev"], 0.0)

    def test_calculate_breakdown_only_non_work_items(self):
        """Test calculation when only non-work items are returned"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "issuetype": {"name": "Epic"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 10.0
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        # All should be zero (Epic excluded)
        self.assertEqual(result["positive"]["Dev"], 0.0)
        self.assertEqual(result["positive"]["QA"], 0.0)

    def test_calculate_breakdown_mixed_resolutions_same_issue_type(self):
        """Test calculation with same issue type but different resolutions"""
        self.mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {"key": "TEST-1", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Fixed"}, "customfield_10002": 5.0}},
                {"key": "TEST-2", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Won't Do"}, "customfield_10002": 3.0}},
                {"key": "TEST-3", "fields": {"issuetype": {"name": "Task"}, "resolution": None, "customfield_10002": 2.0}},
            ]
        }
        result = calculate_story_points_breakdown(
            self.mock_client, ["TEST-1"], max_results=1000
        )
        self.assertEqual(result["positive"]["Dev"], 5.0)
        self.assertEqual(result["negative"]["Dev"], 3.0)
        self.assertEqual(result["unresolved"]["Dev"], 2.0)


class TestFormatStoryPointsBreakdown(unittest.TestCase):
    """Test story points breakdown formatting with hyperlinks and totals"""

    def test_format_breakdown_basic(self):
        """Test basic breakdown formatting"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        result = format_story_points_breakdown(breakdown)
        self.assertIn("Positive resolutions", result)
        self.assertIn("Dev: 10.0", result)
        self.assertIn("QA: 5.0", result)
        self.assertIn("Negative resolutions", result)
        self.assertIn("Unresolved", result)
        self.assertIn("Total", result)

    def test_format_breakdown_with_hyperlinks(self):
        """Test formatting with hyperlinks"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        issue_keys = ["ERA-48896"]
        jira_url = "https://test.atlassian.net"
        result = format_story_points_breakdown(
            breakdown, issue_keys=issue_keys, jira_base_url=jira_url
        )
        # Check for hyperlinks
        self.assertIn("<a href=", result)
        self.assertIn("target=\"_blank\"", result)
        self.assertIn("jql=", result)
        self.assertIn("test.atlassian.net", result)

    def test_format_breakdown_hyperlinks_zero_values(self):
        """Test that zero values don't have hyperlinks"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 0.0},
            "negative": {"Dev": 0.0, "QA": 0.0},
            "unresolved": {"Dev": 0.0, "QA": 0.0}
        }
        issue_keys = ["ERA-48896"]
        jira_url = "https://test.atlassian.net"
        result = format_story_points_breakdown(
            breakdown, issue_keys=issue_keys, jira_base_url=jira_url
        )
        # 10.0 should have link, 0.0 should not
        self.assertIn("<a href=", result)  # For 10.0
        # Zero values should be plain text
        lines = result.split("\n")
        for line in lines:
            if "Dev: 0.0" in line or "QA: 0.0" in line:
                self.assertNotIn("<a href=", line)

    def test_format_breakdown_no_hyperlinks_missing_url(self):
        """Test that hyperlinks are not created when URL is missing"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        issue_keys = ["ERA-48896"]
        result = format_story_points_breakdown(breakdown, issue_keys=issue_keys, jira_base_url=None)
        # Should not have hyperlinks
        self.assertNotIn("<a href=", result)
        self.assertIn("Dev: 10.0", result)

    def test_format_breakdown_no_hyperlinks_missing_keys(self):
        """Test that hyperlinks are not created when issue keys are missing"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        jira_url = "https://test.atlassian.net"
        result = format_story_points_breakdown(breakdown, issue_keys=None, jira_base_url=jira_url)
        # Should not have hyperlinks
        self.assertNotIn("<a href=", result)

    def test_format_breakdown_total_calculation(self):
        """Test that total is calculated correctly"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        result = format_story_points_breakdown(breakdown)
        # Total Dev = 10 + 3 + 7 = 20
        # Total QA = 5 + 2 + 1 = 8
        self.assertIn("Total", result)
        self.assertIn("Dev: 20.0", result)
        self.assertIn("QA: 8.0", result)

    def test_format_breakdown_total_zero(self):
        """Test total calculation with all zeros"""
        breakdown = {
            "positive": {"Dev": 0.0, "QA": 0.0},
            "negative": {"Dev": 0.0, "QA": 0.0},
            "unresolved": {"Dev": 0.0, "QA": 0.0}
        }
        result = format_story_points_breakdown(breakdown)
        self.assertIn("Total", result)
        self.assertIn("Dev: 0.0", result)
        self.assertIn("QA: 0.0", result)

    def test_format_breakdown_bold_headers(self):
        """Test that category headers are bold"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        result = format_story_points_breakdown(breakdown)
        self.assertIn("<b>Positive resolutions</b>", result)
        self.assertIn("<b>Negative resolutions</b>", result)
        self.assertIn("<b>Unresolved</b>", result)
        # Total should NOT be bold
        self.assertIn("Total", result)
        self.assertNotIn("<b>Total</b>", result)

    def test_format_breakdown_zero_values(self):
        """Test formatting with zero values"""
        breakdown = {
            "positive": {"Dev": 0.0, "QA": 0.0},
            "negative": {"Dev": 0.0, "QA": 0.0},
            "unresolved": {"Dev": 0.0, "QA": 0.0}
        }
        result = format_story_points_breakdown(breakdown)
        self.assertIn("Dev: 0.0", result)
        self.assertIn("QA: 0.0", result)

    def test_format_breakdown_missing_keys(self):
        """Test formatting with missing keys"""
        breakdown = {
            "positive": {},
            "negative": {},
            "unresolved": {}
        }
        result = format_story_points_breakdown(breakdown)
        # Should handle missing keys gracefully
        self.assertIn("Positive resolutions", result)
        self.assertIn("Total", result)

    def test_format_breakdown_large_numbers(self):
        """Test formatting with large story point values"""
        breakdown = {
            "positive": {"Dev": 999.5, "QA": 500.25},
            "negative": {"Dev": 100.0, "QA": 50.0},
            "unresolved": {"Dev": 200.75, "QA": 100.5}
        }
        result = format_story_points_breakdown(breakdown)
        self.assertIn("Dev: 999.5", result)
        self.assertIn("QA: 500.25", result)
        # Total should be correct
        self.assertIn("Dev: 1300.25", result)  # 999.5 + 100.0 + 200.75
        self.assertIn("QA: 650.75", result)  # 500.25 + 50.0 + 100.5

    def test_format_breakdown_decimal_precision(self):
        """Test formatting preserves decimal precision"""
        breakdown = {
            "positive": {"Dev": 10.333, "QA": 5.666},
            "negative": {"Dev": 3.111, "QA": 2.222},
            "unresolved": {"Dev": 7.999, "QA": 1.888}
        }
        result = format_story_points_breakdown(breakdown)
        # Should preserve decimals
        self.assertIn("10.333", result)
        self.assertIn("5.666", result)

    def test_format_breakdown_url_encoding(self):
        """Test that JQL queries are properly URL encoded in hyperlinks"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        issue_keys = ["ERA-48896"]
        jira_url = "https://test.atlassian.net"
        result = format_story_points_breakdown(
            breakdown, issue_keys=issue_keys, jira_base_url=jira_url
        )
        # Check URL encoding
        from urllib.parse import unquote
        # Extract URLs and verify they can be decoded
        import re
        urls = re.findall(r'href="([^"]+)"', result)
        for url in urls:
            if "jql=" in url:
                # Should be able to decode
                decoded = unquote(url.split("jql=")[1])
                self.assertIsInstance(decoded, str)

    def test_format_breakdown_jira_url_trailing_slash(self):
        """Test that JIRA URL trailing slashes are handled correctly"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        issue_keys = ["ERA-48896"]
        jira_url_with_slash = "https://test.atlassian.net/"
        result = format_story_points_breakdown(
            breakdown, issue_keys=issue_keys, jira_base_url=jira_url_with_slash
        )
        # Should not have double slashes
        self.assertNotIn("//issues", result)
        self.assertIn("/issues/?jql=", result)


class TestNFRPerformance(unittest.TestCase):
    """Non-Functional Requirements: Performance tests"""

    def test_calculate_breakdown_performance_large_dataset(self):
        """Test performance with large number of issues"""
        import time
        issues = []
        for i in range(500):
            issues.append({
                "key": f"TEST-{i}",
                "fields": {
                    "issuetype": {"name": "Task" if i % 2 == 0 else "Test"},
                    "resolution": {"name": "Done" if i % 3 == 0 else None},
                    "customfield_10002": float(i % 10)
                }
            })
        
        mock_client = Mock()
        mock_client.execute_jql = Mock(return_value={
            "success": True,
            "issues": issues
        })
        
        start_time = time.time()
        result = calculate_story_points_breakdown(
            mock_client, ["TEST-1"], max_results=2000
        )
        end_time = time.time()
        
        # Should complete in reasonable time (< 5 seconds for 500 issues)
        self.assertLess(end_time - start_time, 5.0)
        self.assertIn("positive", result)
        self.assertIn("negative", result)

    def test_format_breakdown_performance_many_categories(self):
        """Test formatting performance with many categories"""
        import time
        breakdown = {
            "positive": {"Dev": 1000.0, "QA": 500.0},
            "negative": {"Dev": 200.0, "QA": 100.0},
            "unresolved": {"Dev": 300.0, "QA": 150.0}
        }
        
        start_time = time.time()
        for _ in range(100):
            result = format_story_points_breakdown(breakdown)
        end_time = time.time()
        
        # Should format quickly (< 1 second for 100 iterations)
        self.assertLess(end_time - start_time, 1.0)


class TestCornerCases(unittest.TestCase):
    """Test corner cases and edge conditions"""

    def test_calculate_breakdown_all_zeros(self):
        """Test calculation when all story points are zero"""
        mock_client = Mock()
        mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 0.0
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            mock_client, ["TEST-1"], max_results=1000
        )
        self.assertEqual(result["positive"]["Dev"], 0.0)

    def test_calculate_breakdown_only_non_work_items(self):
        """Test calculation when only non-work items are returned"""
        mock_client = Mock()
        mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "issuetype": {"name": "Epic"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 10.0
                    }
                }
            ]
        }
        result = calculate_story_points_breakdown(
            mock_client, ["TEST-1"], max_results=1000
        )
        # All should be zero (Epic excluded)
        self.assertEqual(result["positive"]["Dev"], 0.0)
        self.assertEqual(result["positive"]["QA"], 0.0)

    def test_calculate_breakdown_mixed_resolutions_same_issue_type(self):
        """Test calculation with same issue type but different resolutions"""
        mock_client = Mock()
        mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {"key": "TEST-1", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Fixed"}, "customfield_10002": 5.0}},
                {"key": "TEST-2", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Won't Do"}, "customfield_10002": 3.0}},
                {"key": "TEST-3", "fields": {"issuetype": {"name": "Task"}, "resolution": None, "customfield_10002": 2.0}},
            ]
        }
        result = calculate_story_points_breakdown(
            mock_client, ["TEST-1"], max_results=1000
        )
        self.assertEqual(result["positive"]["Dev"], 5.0)
        self.assertEqual(result["negative"]["Dev"], 3.0)
        self.assertEqual(result["unresolved"]["Dev"], 2.0)

    def test_format_breakdown_missing_all_categories(self):
        """Test formatting when all categories are missing"""
        breakdown = {}
        result = format_story_points_breakdown(breakdown)
        # Should handle gracefully
        self.assertIsInstance(result, str)

    def test_format_breakdown_partial_categories(self):
        """Test formatting when only some categories exist"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0}
            # Missing negative and unresolved
        }
        result = format_story_points_breakdown(breakdown)
        self.assertIn("Positive resolutions", result)
        # Should handle missing categories gracefully
        self.assertIn("Total", result)

    def test_get_story_points_none_field_id(self):
        """Test story points extraction when field ID is None"""
        issue = {
            "key": "TEST-123",
            "fields": {"customfield_10016": 5.0}
        }
        result = get_story_points(issue, None)
        # Should fallback to common field IDs
        self.assertEqual(result, 5.0)

    def test_build_jql_single_character_key(self):
        """Test JQL building with single character issue key"""
        keys = ["A"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("A", jql)

    def test_build_jql_very_long_key(self):
        """Test JQL building with very long issue key"""
        keys = ["VERY-LONG-PROJECT-KEY-123456789"]
        jql = build_related_tickets_jql(keys)
        self.assertIn("VERY-LONG-PROJECT-KEY-123456789", jql)


class TestNegativeCases(unittest.TestCase):
    """Test negative cases and error conditions"""

    def test_calculate_breakdown_client_none(self):
        """Test calculation with None client"""
        with self.assertRaises((AttributeError, TypeError)):
            calculate_story_points_breakdown(None, ["TEST-1"])

    def test_calculate_breakdown_invalid_max_results(self):
        """Test calculation with invalid max_results"""
        mock_client = Mock()
        mock_client.execute_jql.return_value = {"success": True, "issues": []}
        # Should handle gracefully
        result = calculate_story_points_breakdown(
            mock_client, ["TEST-1"], max_results=-1
        )
        self.assertIn("positive", result)

    def test_format_breakdown_invalid_breakdown_type(self):
        """Test formatting with invalid breakdown type"""
        with self.assertRaises((AttributeError, TypeError)):
            format_story_points_breakdown(None)

    def test_format_breakdown_invalid_url(self):
        """Test formatting with invalid JIRA URL"""
        breakdown = {
            "positive": {"Dev": 10.0, "QA": 5.0},
            "negative": {"Dev": 3.0, "QA": 2.0},
            "unresolved": {"Dev": 7.0, "QA": 1.0}
        }
        issue_keys = ["ERA-48896"]
        invalid_url = "not-a-valid-url"
        # Should handle gracefully (no hyperlinks)
        result = format_story_points_breakdown(
            breakdown, issue_keys=issue_keys, jira_base_url=invalid_url
        )
        self.assertIsInstance(result, str)

    def test_get_story_points_invalid_issue_structure(self):
        """Test story points extraction with invalid issue structure"""
        invalid_issues = [
            None,
            {},
            {"key": "TEST-1"},  # No fields
            {"fields": None},
            {"fields": {}},
        ]
        for issue in invalid_issues:
            result = get_story_points(issue, "customfield_10002")
            self.assertEqual(result, 0.0)

    def test_build_jql_none_keys(self):
        """Test JQL building with None keys"""
        with self.assertRaises((TypeError, AttributeError)):
            build_related_tickets_jql(None)

    def test_build_jql_invalid_key_format(self):
        """Test JQL building with invalid key format"""
        keys = [""]  # Empty string
        jql = build_related_tickets_jql(keys)
        # Should handle gracefully
        self.assertIsInstance(jql, str)

    def test_categorize_resolution_invalid_input(self):
        """Test resolution categorization with invalid input"""
        # Should handle gracefully
        try:
            result = categorize_resolution(123)  # Not a string
            self.assertIn(result, ["positive", "negative", "unresolved"])
        except (AttributeError, TypeError):
            # Also acceptable - may raise exception
            pass

    def test_is_work_item_invalid_input(self):
        """Test work item check with invalid input"""
        # Should handle gracefully
        try:
            result = is_work_item(123)  # Not a string
            self.assertIsInstance(result, bool)
        except (AttributeError, TypeError):
            # Also acceptable - may raise exception
            pass


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and real-world use cases"""

    def test_full_workflow_single_issue(self):
        """Test complete workflow for a single issue"""
        mock_client = Mock()
        mock_client.base_url = "https://test.atlassian.net"
        mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "issuetype": {"name": "Task"},
                        "resolution": {"name": "Done"},
                        "customfield_10002": 5.0
                    }
                }
            ]
        }
        
        # Calculate breakdown
        breakdown = calculate_story_points_breakdown(
            mock_client, ["TEST-1"], max_results=1000
        )
        
        # Format with hyperlinks
        formatted = format_story_points_breakdown(
            breakdown,
            issue_keys=["TEST-1"],
            jira_base_url=mock_client.base_url,
            positive_resolutions={"Done", "Fixed"}
        )
        
        # Verify results
        self.assertEqual(breakdown["positive"]["Dev"], 5.0)
        self.assertIn("Positive resolutions", formatted)
        self.assertIn("<a href=", formatted)

    def test_full_workflow_multiple_issues(self):
        """Test complete workflow for multiple issues"""
        mock_client = Mock()
        mock_client.base_url = "https://test.atlassian.net"
        mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {"key": "TEST-1", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Done"}, "customfield_10002": 5.0}},
                {"key": "TEST-2", "fields": {"issuetype": {"name": "Test"}, "resolution": {"name": "Done"}, "customfield_10002": 3.0}},
                {"key": "TEST-3", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Won't Do"}, "customfield_10002": 2.0}},
            ]
        }
        
        breakdown = calculate_story_points_breakdown(
            mock_client, ["TEST-1", "TEST-2"], max_results=1000
        )
        
        formatted = format_story_points_breakdown(
            breakdown,
            issue_keys=["TEST-1", "TEST-2"],
            jira_base_url=mock_client.base_url
        )
        
        # Verify all categories
        self.assertEqual(breakdown["positive"]["Dev"], 5.0)
        self.assertEqual(breakdown["positive"]["QA"], 3.0)
        self.assertEqual(breakdown["negative"]["Dev"], 2.0)
        self.assertIn("Total", formatted)

    def test_workflow_with_epic_exclusion(self):
        """Test workflow ensures Epic is excluded from calculation"""
        mock_client = Mock()
        mock_client.base_url = "https://test.atlassian.net"
        mock_client.execute_jql.return_value = {
            "success": True,
            "issues": [
                {"key": "TEST-1", "fields": {"issuetype": {"name": "Task"}, "resolution": {"name": "Done"}, "customfield_10002": 5.0}},
                {"key": "EPIC-1", "fields": {"issuetype": {"name": "Epic"}, "resolution": {"name": "Done"}, "customfield_10002": 100.0}},
            ]
        }
        
        breakdown = calculate_story_points_breakdown(
            mock_client, ["TEST-1"], max_results=1000
        )
        
        # Epic should be excluded
        self.assertEqual(breakdown["positive"]["Dev"], 5.0)
        self.assertNotEqual(breakdown["positive"]["Dev"], 105.0)


if __name__ == "__main__":
    unittest.main()
