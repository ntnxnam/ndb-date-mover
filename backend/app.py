"""
Flask Backend API Server for JIRA Connection Testing

This application provides a REST API to test JIRA connections using
Personal Access Token (PAT) authentication.

Author: NDB Date Mover Team
"""

import logging
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from jira_client import JiraClient, create_jira_client

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
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Ensure JSON responses are properly formatted
@app.after_request
def after_request(response):
    """Ensure all API responses are JSON."""
    if request.path.startswith('/api/'):
        response.headers['Content-Type'] = 'application/json'
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

