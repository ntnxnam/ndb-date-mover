"""
Story Points Calculator Module

Calculates story points breakdown by issue type and resolution (positive/negative)
for all tickets related to a given set of issue keys.

Author: NDB Date Mover Team
"""

import logging
from typing import Dict, List, Set, Tuple
from backend.jira_client import JiraClient

logger = logging.getLogger(__name__)

# Default positive resolutions (can be configured)
# Positive: Fixed, Done, Resolved, Complete
DEFAULT_POSITIVE_RESOLUTIONS = {
    "Fixed", "Done", "Resolved", "Complete"
}

# Negative resolutions are everything else (except unresolved)
# We don't need to list them - anything that's not positive and not None is negative

# Issue type categories (for Dev/QA grouping)
# Dev = issueType NOT IN (Test, Test Plan)
# QA = issueType IN (Test, Test Plan)
ISSUE_CATEGORY_DEV = "Dev"
ISSUE_CATEGORY_QA = "QA"

# Non-work-item issue types to exclude from story points calculation
# Work items are: Task, Bug, Test, Test Plan, DevDocs, etc.
# Non-work items are: Epic, Feature, Initiative, X-FEAT, Capability, etc.
NON_WORK_ITEM_TYPES = {
    "Epic", "Feature", "Initiative", "X-FEAT", "Capability",
    "epic", "feature", "initiative", "x-feat", "capability"
}

# Common story points field IDs (JIRA typically uses customfield_10002)
# This will be configurable or auto-detected
STORY_POINTS_FIELD_IDS = ["customfield_10002", "customfield_10016", "customfield_10020"]


def build_related_tickets_jql(issue_keys: List[str]) -> str:
    """
    Build a complex JQL query to fetch all related tickets for given issue keys.
    
    The query includes:
    - Direct key matches
    - Parent Link (customfield_20363)
    - FEAT ID and FEAT Number fields
    - Portfolio children
    - Issues in epics
    - Subtasks
    
    Args:
        issue_keys: List of JIRA issue keys (e.g., ["ERA-48896", "ERA-44920"])
        
    Returns:
        str: JQL query string
    """
    if not issue_keys:
        return ""
    
    # Build key list for IN clause
    keys_str = ", ".join(issue_keys)
    
    # Build the complex JQL query
    jql_parts = [
        f"key IN ({keys_str})",
        f'("Parent Link" IN ({keys_str}))',
        f'("FEAT ID" ~ "{keys_str}")',
        f'("FEAT Number" IN ({keys_str}))',
    ]
    
    # Add portfolio children and epic-related queries for each key
    for key in issue_keys:
        jql_parts.append(f'(issueFunction in portfolioChildrenOf("key={key}"))')
        jql_parts.append(
            f'(issueFunction in issuesInEpics("issueFunction in portfolioChildrenOf(\'key={key}\')"))'
        )
        jql_parts.append(f'(issueFunction in subtasksOf("key={key}"))')
        jql_parts.append(
            f'issueFunction in subtasksOf("issueFunction in issuesInEpics(\\"issueFunction in portfolioChildrenOf(\\\'key={key}\\\') \\")")'
        )
    
    # Combine with OR
    jql = " OR ".join(jql_parts)
    
    logger.debug(f"Built JQL query for {len(issue_keys)} keys: {jql[:200]}...")
    return jql


def is_work_item(issue_type_name: str) -> bool:
    """
    Check if an issue type is a work item (should be included in story points calculation).
    
    Work items: Task, Bug, Test, Test Plan, DevDocs, etc.
    Non-work items: Epic, Feature, Initiative, X-FEAT, Capability, etc.
    
    Args:
        issue_type_name: Issue type name from JIRA
        
    Returns:
        bool: True if it's a work item, False otherwise
    """
    if not issue_type_name:
        return True  # Default to including if unknown
    
    issue_type_lower = issue_type_name.lower()
    
    # Exclude non-work-item types
    if issue_type_lower in NON_WORK_ITEM_TYPES:
        return False
    
    # Check for common non-work-item patterns
    if any(non_work in issue_type_lower for non_work in ["epic", "feature", "initiative", "x-feat", "capability"]):
        return False
    
    return True


def categorize_issue_for_dev_qa(issue_type_name: str) -> str:
    """
    Categorize issue type into Dev or QA.
    
    Dev = issueType NOT IN (Test, Test Plan)
    QA = issueType IN (Test, Test Plan)
    
    Args:
        issue_type_name: Issue type name from JIRA
        
    Returns:
        str: "Dev" or "QA"
    """
    if not issue_type_name:
        return ISSUE_CATEGORY_DEV  # Default to Dev if unknown
    
    issue_type_lower = issue_type_name.lower()
    
    # Check if it's a Test or Test Plan issue type
    if "test" in issue_type_lower and "plan" in issue_type_lower:
        return ISSUE_CATEGORY_QA
    elif issue_type_lower == "test" or issue_type_lower == "test plan":
        return ISSUE_CATEGORY_QA
    else:
        return ISSUE_CATEGORY_DEV


def categorize_resolution(resolution_name: str, 
                         positive_resolutions: Set[str] = None) -> str:
    """
    Categorize resolution as positive, negative, or unresolved.
    
    Positive: Fixed, Done, Resolved, Complete (configurable)
    Negative: Everything else that has a resolution (not None)
    Unresolved: No resolution (None or empty)
    
    Args:
        resolution_name: Resolution name from JIRA (can be None)
        positive_resolutions: Set of positive resolution names
        
    Returns:
        str: "positive", "negative", or "unresolved"
    """
    if not resolution_name:
        return "unresolved"
    
    positive = positive_resolutions or DEFAULT_POSITIVE_RESOLUTIONS
    
    resolution_lower = resolution_name.lower()
    
    # Check positive resolutions
    for pos_res in positive:
        if pos_res.lower() == resolution_lower:
            return "positive"
    
    # If it has a resolution but is not positive, it's negative
    return "negative"


def get_story_points(issue: Dict, story_points_field_id: str = None) -> float:
    """
    Extract story points from an issue.
    
    Args:
        issue: JIRA issue dictionary
        story_points_field_id: Custom field ID for story points (auto-detect if None)
        
    Returns:
        float: Story points value (0 if not found)
    """
    fields = issue.get("fields", {})
    issue_key = issue.get("key", "UNKNOWN")
    
    # Try provided field ID first
    if story_points_field_id:
        value = fields.get(story_points_field_id)
        if value is not None:
            try:
                result = float(value) if value else 0.0
                if result > 0:
                    logger.debug(f"Found story points for {issue_key} in {story_points_field_id}: {result}")
                return result
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not convert story points value for {issue_key} from {story_points_field_id}: {value} (error: {e})")
        else:
            logger.debug(f"No story points found for {issue_key} in configured field {story_points_field_id}")
    
    # Try common story points field IDs (including customfield_10002)
    for field_id in STORY_POINTS_FIELD_IDS:
        if fields.get(field_id) is not None:
            value = fields.get(field_id)
            try:
                result = float(value) if value else 0.0
                if result > 0:
                    logger.debug(f"Found story points for {issue_key} in {field_id}: {result}")
                return result
            except (ValueError, TypeError):
                continue
    
    # Log if no story points found
    logger.debug(f"No story points found for {issue_key} in any known field. Available custom fields: {[k for k in fields.keys() if 'customfield' in k.lower()][:10]}")
    
    return 0.0


def calculate_story_points_breakdown(
    client: JiraClient,
    issue_keys: List[str],
    story_points_field_id: str = None,
    positive_resolutions: Set[str] = None,
    max_results: int = 1000
) -> Dict:
    """
    Calculate story points breakdown for all tickets related to given issue keys.
    
    Args:
        client: JIRA client instance
        issue_keys: List of JIRA issue keys to find related tickets for
        story_points_field_id: Custom field ID for story points
        positive_resolutions: Set of positive resolution names (default: Fixed, Done, Resolved, Complete)
        max_results: Maximum number of results to fetch
        
    Returns:
        Dict: Story points breakdown with structure:
        {
            "positive": {
                "total_count": int,
                "total_story_points": float,
                "Task": {"count": int, "story_points": float},
                "Bug": {"count": int, "story_points": float},
                "Test": {"count": int, "story_points": float},
                "Improvement": {"count": int, "story_points": float},
                "Other": {"count": int, "story_points": float}
            },
            "negative": {
                "total_count": int,
                "total_story_points": float,
                "Task": {"count": int, "story_points": float},
                ...
            },
            "unresolved": {
                "total_count": int,
                "total_story_points": float,
                "Task": {"count": int, "story_points": float},
                ...
            }
        }
    """
    if not issue_keys:
        return {
            "positive": {
                "total_count": 0,
                "total_story_points": 0.0,
                "Task": {"count": 0, "story_points": 0.0},
                "Bug": {"count": 0, "story_points": 0.0},
                "Test": {"count": 0, "story_points": 0.0},
                "Improvement": {"count": 0, "story_points": 0.0},
                "Other": {"count": 0, "story_points": 0.0}
            },
            "negative": {
                "total_count": 0,
                "total_story_points": 0.0,
                "Task": {"count": 0, "story_points": 0.0},
                "Bug": {"count": 0, "story_points": 0.0},
                "Test": {"count": 0, "story_points": 0.0},
                "Improvement": {"count": 0, "story_points": 0.0},
                "Other": {"count": 0, "story_points": 0.0}
            },
            "unresolved": {
                "total_count": 0,
                "total_story_points": 0.0,
                "Task": {"count": 0, "story_points": 0.0},
                "Bug": {"count": 0, "story_points": 0.0},
                "Test": {"count": 0, "story_points": 0.0},
                "Improvement": {"count": 0, "story_points": 0.0},
                "Other": {"count": 0, "story_points": 0.0}
            }
        }
    
    logger.info(f"Calculating story points for {len(issue_keys)} issue keys")
    
    # Build JQL query
    jql = build_related_tickets_jql(issue_keys)
    
    # Execute query - only fetch minimal fields needed for story points calculation
    # We do NOT fetch changelog/history for related tickets - only basic fields
    # Fields needed: issuetype, resolution, story points field (customfield_10002)
    minimal_fields = "issuetype,resolution,customfield_10002,key"
    try:
        result = client.execute_jql(jql, max_results=max_results, start_at=0, fields=minimal_fields)
        
        if not result.get("success"):
            logger.error(f"Failed to fetch related tickets: {result.get('error')}")
            return {
                "positive": {
                    "Dev": 0.0,
                    "QA": 0.0
                },
                "negative": {
                    "Dev": 0.0,
                    "QA": 0.0
                },
                "unresolved": {
                    "Dev": 0.0,
                    "QA": 0.0
                },
                "error": result.get("error", "Unknown error")
            }
        
        issues = result.get("issues", [])
        logger.info(f"Fetched {len(issues)} related tickets")
        
        # Initialize breakdown structure (Dev/QA grouping, story points only)
        breakdown = {
            "positive": {
                "Dev": 0.0,
                "QA": 0.0
            },
            "negative": {
                "Dev": 0.0,
                "QA": 0.0
            },
            "unresolved": {
                "Dev": 0.0,
                "QA": 0.0
            }
        }
        
        # Process each issue
        for issue in issues:
            fields = issue.get("fields", {})
            
            # Get issue type
            issue_type_obj = fields.get("issuetype", {})
            issue_type_name = issue_type_obj.get("name", "") if isinstance(issue_type_obj, dict) else str(issue_type_obj)
            
            # Skip non-work items (Epic, Feature, Initiative, X-FEAT, Capability, etc.)
            if not is_work_item(issue_type_name):
                logger.debug(f"Skipping non-work item: {issue_type_name} (key: {issue.get('key', 'UNKNOWN')})")
                continue
            
            # Categorize as Dev or QA
            dev_qa_category = categorize_issue_for_dev_qa(issue_type_name)
            
            # Get resolution
            resolution_obj = fields.get("resolution", {})
            resolution_name = resolution_obj.get("name", "") if isinstance(resolution_obj, dict) else (str(resolution_obj) if resolution_obj else None)
            resolution_category = categorize_resolution(
                resolution_name, positive_resolutions
            )
            
            # Get story points
            story_points = get_story_points(issue, story_points_field_id)
            
            # Update breakdown (only story points, grouped by Dev/QA)
            category_breakdown = breakdown[resolution_category]
            category_breakdown[dev_qa_category] += story_points
        
        logger.info(f"Story points breakdown calculated: Positive Dev={breakdown['positive']['Dev']}, QA={breakdown['positive']['QA']}, Negative Dev={breakdown['negative']['Dev']}, QA={breakdown['negative']['QA']}, Unresolved Dev={breakdown['unresolved']['Dev']}, QA={breakdown['unresolved']['QA']}")
        return breakdown
        
    except Exception as e:
        logger.exception(f"Error calculating story points breakdown: {str(e)}")
        return {
            "positive": {
                "Dev": 0.0,
                "QA": 0.0
            },
            "negative": {
                "Dev": 0.0,
                "QA": 0.0
            },
            "unresolved": {
                "Dev": 0.0,
                "QA": 0.0
            },
            "error": str(e)
        }


def build_jql_for_category(
    issue_keys: List[str],
    resolution_category: str,
    dev_qa_category: str,
    positive_resolutions: Set[str] = None
) -> str:
    """
    Build JQL query for a specific category (e.g., positive Dev, negative QA).
    
    Args:
        issue_keys: Original issue keys to find related tickets
        resolution_category: "positive", "negative", or "unresolved"
        dev_qa_category: "Dev" or "QA"
        positive_resolutions: Set of positive resolution names
        
    Returns:
        str: JQL query string
    """
    # Build base query for related tickets
    base_jql = build_related_tickets_jql(issue_keys)
    
    # Add work item filter (exclude Epic, Feature, etc.)
    work_item_filter = 'issuetype NOT IN ("Epic", "Feature", "Initiative", "X-FEAT", "Capability")'
    
    # Add Dev/QA filter
    if dev_qa_category == "QA":
        dev_qa_filter = 'issuetype IN ("Test", "Test Plan")'
    else:  # Dev
        dev_qa_filter = 'issuetype NOT IN ("Test", "Test Plan")'
    
    # Add resolution filter
    positive = positive_resolutions or DEFAULT_POSITIVE_RESOLUTIONS
    if resolution_category == "positive":
        # Build resolution list: "Fixed", "Done", etc.
        resolution_list = ", ".join([f'"{r}"' for r in positive])
        resolution_filter = f'resolution IN ({resolution_list})'
    elif resolution_category == "negative":
        # Negative = has resolution but not in positive list
        resolution_list = ", ".join([f'"{r}"' for r in positive])
        resolution_filter = f'resolution IS NOT EMPTY AND resolution NOT IN ({resolution_list})'
    else:  # unresolved
        resolution_filter = 'resolution IS EMPTY'
    
    # Combine all filters
    jql = f'({base_jql}) AND {work_item_filter} AND {dev_qa_filter} AND {resolution_filter}'
    
    return jql


def format_story_points_breakdown(
    breakdown: Dict,
    issue_keys: List[str] = None,
    jira_base_url: str = None,
    positive_resolutions: Set[str] = None
) -> str:
    """
    Format story points breakdown as a display string with hyperlinks.
    
    New format: Show only story points, grouped by Dev/QA
    - Dev = issueType NOT IN (Test, Test Plan)
    - QA = issueType IN (Test, Test Plan)
    - Story points are hyperlinked to JQL queries
    - Total section shows sum of all categories
    
    Args:
        breakdown: Story points breakdown dictionary
        issue_keys: Original issue keys (for building JQL links)
        jira_base_url: JIRA base URL (for building hyperlinks)
        positive_resolutions: Set of positive resolution names (for JQL)
        
    Returns:
        str: Formatted string for display (HTML format for hyperlinks)
    """
    lines = []
    
    # Helper function to create hyperlink
    def create_link(value: float, category: str, resolution: str) -> str:
        """Create hyperlink for story points value"""
        if value == 0.0 or not issue_keys or not jira_base_url:
            return str(value)
        
        # Build JQL query for this category
        jql = build_jql_for_category(issue_keys, resolution, category, positive_resolutions)
        
        # URL encode the JQL query
        from urllib.parse import quote
        encoded_jql = quote(jql)
        
        # Create JIRA search URL
        jira_url = f"{jira_base_url.rstrip('/')}/issues/?jql={encoded_jql}"
        
        return f'<a href="{jira_url}" target="_blank">{value}</a>'
    
    # Positive resolutions
    pos = breakdown.get("positive", {})
    pos_dev = pos.get('Dev', 0.0)
    pos_qa = pos.get('QA', 0.0)
    lines.append(f"<b>Positive resolutions</b>")
    lines.append(f"Dev: {create_link(pos_dev, 'Dev', 'positive')}")
    lines.append(f"QA: {create_link(pos_qa, 'QA', 'positive')}")
    
    # Negative resolutions
    neg = breakdown.get("negative", {})
    neg_dev = neg.get('Dev', 0.0)
    neg_qa = neg.get('QA', 0.0)
    lines.append("")
    lines.append(f"<b>Negative resolutions</b>")
    lines.append(f"Dev: {create_link(neg_dev, 'Dev', 'negative')}")
    lines.append(f"QA: {create_link(neg_qa, 'QA', 'negative')}")
    
    # Unresolved
    unres = breakdown.get("unresolved", {})
    unres_dev = unres.get('Dev', 0.0)
    unres_qa = unres.get('QA', 0.0)
    lines.append("")
    lines.append(f"<b>Unresolved</b>")
    lines.append(f"Dev: {create_link(unres_dev, 'Dev', 'unresolved')}")
    lines.append(f"QA: {create_link(unres_qa, 'QA', 'unresolved')}")
    
    # Total (normal font, not bold)
    total_dev = pos_dev + neg_dev + unres_dev
    total_qa = pos_qa + neg_qa + unres_qa
    lines.append("")
    lines.append(f"Total")
    lines.append(f"Dev: {total_dev}")
    lines.append(f"QA: {total_qa}")
    
    return "\n".join(lines)

