#!/usr/bin/env python3
"""
Simple HTTP Server for Frontend

This server serves the static frontend files and can be configured
to proxy API requests to the backend server.

Author: NDB Date Mover Team
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Get the frontend directory
FRONTEND_DIR = Path(__file__).parent
# Using unusual port 6291 to avoid conflicts with common services
PORT = int(os.getenv("FRONTEND_PORT", "6291"))


class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for serving frontend files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self):
        """Add CORS headers."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[Frontend Server] {format % args}")


def main():
    """Start the frontend server."""
    os.chdir(FRONTEND_DIR)
    
    with socketserver.TCPServer(("", PORT), FrontendHandler) as httpd:
        backend_port = os.getenv("BACKEND_PORT", "8473")
        print(f"🚀 Frontend server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {FRONTEND_DIR}")
        print(f"🔗 Backend API should be at: http://localhost:{backend_port}")
        print("\nPress Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down frontend server...")
            sys.exit(0)


if __name__ == "__main__":
    main()

