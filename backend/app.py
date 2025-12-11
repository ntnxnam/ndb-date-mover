"""
Flask Backend API Server for JIRA Connection Testing

This application provides a REST API to test JIRA connections using
Personal Access Token (PAT) authentication.

Author: NDB Date Mover Team
"""

import logging
import os
from typing import Dict, List
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from backend.jira_client import JiraClient, create_jira_client
from backend.config_loader import ConfigLoader, load_config
from backend.date_utils import (
    format_date,
    calculate_week_slip,
    extract_date_history,
    get_week_slip_color,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("jira_connection.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Enable CORS for frontend - allow all origins for development
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/health": {"origins": "*"}
}, supports_credentials=True)

# Ensure JSON responses are properly formatted
@app.after_request
def after_request(response):
    """Ensure all API responses are JSON."""
    if request.path.startswith('/api/'):
        # Only set JSON content type if not already set and response has content
        if response.content_length:
            # Check if Content-Type is already set (case-insensitive)
            content_type_set = any(
                h.lower() == 'content-type' 
                for h in response.headers.keys()
            )
            if not content_type_set:
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


@app.route("/api/test-connection", methods=["POST"])
def test_connection():
    """
    API endpoint to test JIRA connection.

    This endpoint creates a JiraClient instance and tests the connection
    to JIRA using the credentials from environment variables.

    Returns:
        JSON response with connection test results
    """
    logger.info("Connection test requested")

    try:
        # Create JIRA client from environment variables
        client = create_jira_client()

        if client is None:
            logger.error("Failed to create JIRA client - missing environment variables")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "JIRA credentials not configured. Please check your .env file.",
                    }
                ),
                400,
            )

        # Use context manager to ensure proper cleanup
        success = False
        result = {}
        try:
            # Test the connection
            success, result = client.test_connection()

            # Optionally get user info if connection is successful
            if success:
                user_info = client.get_user_info()
                if user_info:
                    result["user"] = {
                        "display_name": user_info.get("displayName"),
                        "email": user_info.get("emailAddress"),
                        "account_id": user_info.get("accountId"),
                    }
        finally:
            # Ensure session is always closed
            client.close()

        # Ensure result is always a valid dict
        if not result:
            result = {
                "success": False,
                "message": "Unknown error occurred during connection test"
            }

        # Log the result
        if success:
            logger.info(f"Connection test successful: {result.get('message')}")
        else:
            logger.warning(f"Connection test failed: {result.get('message')}")

        # Return appropriate HTTP status code
        status_code = 200 if success else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.exception("Unexpected error during connection test")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Unexpected error: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/query", methods=["POST"])
def execute_query():
    """
    Execute a JQL query against JIRA and enrich with date history and week slips.
    
    Request body:
        {
            "jql": "project = PROJ AND status = 'In Progress'",
            "max_results": 100,
            "start_at": 0,
            "include_history": true
        }
    
    Returns:
        JSON response with query results enriched with date history
    """
    logger.info("JQL query execution requested")
    
    try:
        # Get request data
        data = request.get_json() or {}
        jql = data.get("jql", "").strip()
        max_results = data.get("max_results", 100)
        start_at = data.get("start_at", 0)
        include_history = data.get("include_history", True)
        
        if not jql:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "JQL query is required",
                    }
                ),
                400,
            )
        
        # Load configuration
        try:
            config_loader = ConfigLoader()
            config = config_loader.load()
            date_fields = config_loader.get_date_fields()
            date_format = config_loader.get_date_format()
        except Exception as e:
            logger.warning(f"Could not load configuration: {str(e)}")
            date_fields = []
            date_format = "mm/dd/yyyy"  # Display format is always mm/dd/yyyy
        
        # Create JIRA client
        client = create_jira_client()
        if client is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "JIRA credentials not configured",
                    }
                ),
                400,
            )
        
        try:
            # Execute query
            result = client.execute_jql(jql, max_results, start_at)
            
            if not result.get("success"):
                return jsonify(result), 400
            
            # Get field metadata for display names
            field_metadata = client.get_field_metadata()
            
            # Enrich issues with date history and week slips
            enriched_issues = []
            for issue in result.get("issues", []):
                enriched_issue = enrich_issue_with_dates(
                    issue, date_fields, field_metadata, client, include_history, date_format
                )
                enriched_issues.append(enriched_issue)
            
            result["issues"] = enriched_issues
            result["field_metadata"] = {
                field_id: {
                    "name": field_data.get("name", field_id),
                    "type": field_data.get("type", "unknown"),
                }
                for field_id, field_data in field_metadata.items()
            }
            
            # Include display_columns from config so frontend knows which columns to show
            try:
                result["display_columns"] = config_loader.get_display_columns()
            except Exception:
                # Fallback: use all fields if config not available
                result["display_columns"] = None
            
            return jsonify(result), 200
        finally:
            client.close()
            
    except Exception as e:
        logger.exception("Unexpected error during query execution")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                }
            ),
            500,
        )


def enrich_issue_with_dates(
    issue: Dict,
    date_fields: List[Dict],
    field_metadata: Dict,
    client: JiraClient,
    include_history: bool,
    date_format: str,
) -> Dict:
    """
    Enrich an issue with date history and week slip calculations.
    
    Args:
        issue: JIRA issue data
        date_fields: List of date field configurations
        field_metadata: Field metadata dictionary
        client: JIRA client instance
        include_history: Whether to fetch and include history
        date_format: Date format string
        
    Returns:
        Dict: Enriched issue data
    """
    issue_key = issue.get("key", "")
    fields = issue.get("fields", {})
    
    # Process each date field that tracks history
    for date_field_config in date_fields:
        field_id = date_field_config.get("id")
        current_value = fields.get(field_id)
        
        if not current_value:
            continue
        
        # Format current date
        formatted_current = format_date(str(current_value), date_format)
        fields[f"{field_id}_formatted"] = formatted_current
        
        if include_history and date_field_config.get("track_history"):
            try:
                # Fetch changelog for this field
                # Note: We pass field_id to filter, but JIRA may not include fieldId in changelog items
                # So we also filter by matching the normalized field ID in extract_date_history
                changelog = client.get_issue_changelog(issue_key, field_id)
                date_history = extract_date_history(changelog, field_id)
                
                # Format historical dates
                formatted_history = [
                    format_date(date_val, date_format)
                    for date_val, _ in date_history
                    if date_val != current_value
                ]
                
                fields[f"{field_id}_history"] = formatted_history
                
                # Calculate week slip
                if date_history:
                    original_date = date_history[0][0]  # First date in history
                    weeks, week_str = calculate_week_slip(original_date, str(current_value))
                    fields[f"{field_id}_week_slip"] = {
                        "weeks": weeks,
                        "display": week_str,
                        "color": get_week_slip_color(weeks),
                    }
                else:
                    fields[f"{field_id}_week_slip"] = {
                        "weeks": 0,
                        "display": "0 weeks",
                        "color": "gray",
                    }
                    
            except Exception as e:
                logger.warning(
                    f"Error enriching date history for {issue_key}/{field_id}: {str(e)}"
                )
                fields[f"{field_id}_history"] = []
                fields[f"{field_id}_week_slip"] = {
                    "weeks": 0,
                    "display": "N/A",
                    "color": "gray",
                }
    
    issue["fields"] = fields
    return issue


@app.route("/api/fields", methods=["GET"])
def get_fields():
    """
    Get field metadata from JIRA.
    
    Query parameters:
        field_id: Optional specific field ID to fetch
    
    Returns:
        JSON response with field metadata
    """
    logger.info("Field metadata requested")
    
    try:
        field_id = request.args.get("field_id")
        
        # Create JIRA client
        client = create_jira_client()
        if client is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "JIRA credentials not configured",
                    }
                ),
                400,
            )
        
        try:
            # Get field metadata
            fields = client.get_field_metadata(field_id)
            return jsonify({"success": True, "fields": fields}), 200
        finally:
            client.close()
            
    except Exception as e:
        logger.exception("Unexpected error fetching field metadata")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/issue/<issue_id>/history", methods=["GET"])
def get_issue_history(issue_id: str):
    """
    Get changelog (change history) for an issue.
    
    Query parameters:
        field_id: Optional specific field ID to filter changes
    
    Returns:
        JSON response with issue change history
    """
    logger.info(f"Changelog requested for issue: {issue_id}")
    
    try:
        field_id = request.args.get("field_id")
        
        # Create JIRA client
        client = create_jira_client()
        if client is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "JIRA credentials not configured",
                    }
                ),
                400,
            )
        
        try:
            # Get changelog
            changes = client.get_issue_changelog(issue_id, field_id)
            return jsonify({"success": True, "changes": changes}), 200
        finally:
            client.close()
            
    except Exception as e:
        logger.exception("Unexpected error fetching changelog")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/config", methods=["GET"])
def get_config():
    """
    Get the current configuration.
    
    Returns:
        JSON response with configuration data
    """
    try:
        loader = ConfigLoader()
        config = loader.load()
        return jsonify({"success": True, "config": config}), 200
    except FileNotFoundError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                }
            ),
            404,
        )
    except Exception as e:
        logger.exception("Unexpected error loading configuration")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                }
            ),
            500,
        )


@app.route("/health")
def health():
    """
    Health check endpoint.

    Returns:
        JSON response indicating service health
    """
    return jsonify({"status": "healthy", "service": "jira-connection-tester"}), 200


if __name__ == "__main__":
    # Check if required environment variables are set
    jira_url = os.getenv("JIRA_URL")
    jira_token = os.getenv("JIRA_PAT_TOKEN")

    if not jira_url or not jira_token:
        logger.warning(
            "JIRA_URL or JIRA_PAT_TOKEN not set in environment. "
            "Please configure your .env file."
        )

    # Run the Flask app
    # Using unusual port 8473 to avoid conflicts with common services
    backend_port = int(os.getenv("BACKEND_PORT", "8473"))
    logger.info(f"Starting Flask application on port {backend_port}...")
    app.run(debug=True, host="0.0.0.0", port=backend_port)

