# Project Directory Structure

```
ndb-date-mover/
│
├── 📁 backend/                    # Backend API Server
│   ├── 📄 app.py                 # Flask API application
│   ├── 📄 jira_client.py        # JIRA connection module
│   └── 📄 __init__.py           # Backend package init
│
├── 📁 frontend/                   # Frontend Web Server
│   ├── 📄 index.html            # Main UI page
│   └── 📄 server.py            # Simple HTTP server
│
├── 📁 tests/                      # Test suite
│   ├── 📄 __init__.py            # Test package initialization
│   ├── 📄 test_jira_client.py    # JIRA client unit tests
│   └── 📄 test_app.py            # Flask application tests
│
├── 📄 requirements.txt           # Python dependencies
├── 📄 pytest.ini                 # Pytest configuration
├── 📄 .gitignore                 # Git ignore rules (excludes .env)
├── 📄 .flake8                    # Flake8 linting configuration
│
├── 📄 start_backend.sh           # Backend server startup script
├── 📄 start_frontend.sh          # Frontend server startup script
├── 📄 start_all.sh               # Start both servers script
│
├── 📄 README.md                   # Project documentation
├── 📄 QUICKSTART.md              # Quick setup guide
├── 📄 DEPLOYMENT.md              # Deployment guide
├── 📄 CODE_REVIEW.md             # Tech lead code review
└── 📄 PROJECT_STRUCTURE.md       # This file
│
└── 📄 .env                        # Environment variables (NOT in git)
    └── JIRA_URL=...
    └── JIRA_PAT_TOKEN=...
```

## File Descriptions

### Core Application Files
- **`app.py`**: Flask web application with routes for UI and API endpoints
- **`jira_client.py`**: JIRA client module implementing bearer token authentication

### Configuration Files
- **`requirements.txt`**: Python package dependencies
- **`pytest.ini`**: Pytest test runner configuration
- **`.gitignore`**: Files and directories excluded from version control
- **`.flake8`**: Code style linting configuration
- **`.env`**: Environment variables (create this file with your credentials)

### Templates
- **`templates/index.html`**: Single-page web UI for testing JIRA connection

### Tests
- **`tests/test_jira_client.py`**: Comprehensive unit tests for JIRA client
- **`tests/test_app.py`**: Tests for Flask application routes and endpoints

### Documentation
- **`README.md`**: Main project documentation
- **`QUICKSTART.md`**: Quick setup and usage guide
- **`CODE_REVIEW.md`**: Technical code review and best practices
- **`PROJECT_STRUCTURE.md`**: This file - directory structure overview

