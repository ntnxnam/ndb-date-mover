# Project Directory Structure

```
ndb-date-mover/
│
├── 📁 backend/                    # Backend API Server
│   ├── 📄 app.py                 # Flask API application (API-only)
│   ├── 📄 jira_client.py        # JIRA connection module with self-healing
│   ├── 📄 config_loader.py      # Configuration file loader and validator
│   ├── 📄 date_utils.py         # Date formatting and week slip calculations
│   ├── 📄 history_fetcher.py    # Fetches historical date changes for configured fields
│   ├── 📄 ai_summarizer.py     # AI summarization for executive-friendly text
│   ├── 📄 utils.py              # Shared utility functions (error handling)
│   └── 📄 __init__.py           # Backend package init
│
├── 📁 frontend/                   # Frontend Web Server
│   ├── 📄 app.html              # Main application UI (sidebar, navigation, table)
│   ├── 📄 index.html            # Redirects to app.html
│   └── 📄 server.py             # Simple HTTP server with routing
│
├── 📁 config/                     # Configuration Files
│   ├── 📄 fields.json           # Custom field configuration (user-created)
│   └── 📄 fields.json.example   # Example configuration template
│
├── 📁 tests/                      # Test suite
│   ├── 📄 __init__.py            # Test package initialization
│   ├── 📄 test_jira_client.py    # JIRA client unit tests
│   ├── 📄 test_app.py            # Flask application tests
│   ├── 📄 test_config_loader.py  # Configuration loader tests
│   ├── 📄 test_date_utils.py    # Date utility function tests
│   ├── 📄 test_jira_client_json_parsing.py  # JSON parsing error handling tests
│   └── 📄 test_jira_client_filter.py  # Filter ID handling tests
│
├── 📄 requirements.txt           # Python dependencies
├── 📄 pytest.ini                 # Pytest configuration
├── 📄 .gitignore                 # Git ignore rules (excludes .env)
├── 📄 .flake8                    # Flake8 linting configuration
│
├── 📄 start_backend.sh           # Backend server startup script
├── 📄 start_frontend.sh          # Frontend server startup script
├── 📄 start_all.sh               # Start both servers script
├── 📄 start_with_tests.sh        # Start with tests and self-healing
├── 📄 run_tests.sh               # Run test suite
├── 📄 kill_servers.sh            # Kill servers on ports 8473 and 6291
├── 📄 restart.sh                 # Restart servers (runs tests first)
├── 📄 uber.sh                    # Unified control script (start/stop/restart/status/test)
│
├── 📄 README.md                   # Project documentation
├── 📄 CURSOR_PROMPT.md           # Cursor-friendly development prompt
├── 📄 TEST_PLAN.md               # Comprehensive test plan
├── 📄 PROJECT_REQUIREMENTS.md    # Detailed project requirements
├── 📄 PROJECT_STRUCTURE.md        # This file
│
└── 📄 .env                        # Environment variables (NOT in git)
    └── JIRA_URL=...
    └── JIRA_PAT_TOKEN=...
```

## File Descriptions

### Core Application Files
- **`backend/app.py`**: Flask API application (API-only, no UI rendering)
  - Endpoints: `/api/query`, `/api/fields`, `/api/issue/<id>/history`, `/api/config`, `/api/test-connection`, `/health`
- **`backend/jira_client.py`**: JIRA client module with self-healing retry logic
  - Methods: `execute_jql()`, `get_field_metadata()`, `get_issue_changelog()`, `test_connection()`
- **`backend/config_loader.py`**: Configuration file loader and validator
  - Loads and validates `config/fields.json`
- **`backend/date_utils.py`**: Date formatting and week slip calculation utilities
  - Functions: `format_date()`, `calculate_week_slip()`, `extract_date_history()`
- **`backend/history_fetcher.py`**: Fetches historical date changes from JIRA
  - `HistoryFetcher` class - Fetches history only for configured date fields
  - `fetch_history_for_issue()` - Single issue history
  - `fetch_history_for_issues()` - Batch history for multiple issues
  - Only processes fields with `track_history=true` from config
- **`backend/utils.py`**: Shared utility functions for error handling
  - `safe_get_response_text()` - Unified response text extraction
  - `check_html_response()` - HTML response detection

### Frontend Files
- **`frontend/app.html`**: Main application UI with sidebar navigation, JQL query builder, table display
- **`frontend/index.html`**: Redirects to app.html
- **`frontend/server.py`**: Simple HTTP server with routing support

### Configuration Files
- **`config/fields.json`**: User-created configuration for custom fields and display columns
- **`config/fields.json.example`**: Example configuration template
- **`requirements.txt`**: Python package dependencies
- **`pytest.ini`**: Pytest test runner configuration
- **`.gitignore`**: Files and directories excluded from version control
- **`.flake8`**: Code style linting configuration
- **`.env`**: Environment variables (create this file with your credentials)

### Test Files
- **`tests/test_jira_client.py`**: Comprehensive unit tests for JIRA client
- **`tests/test_app.py`**: Tests for Flask application routes and endpoints
- **`tests/test_config_loader.py`**: Configuration loader validation tests
- **`tests/test_date_utils.py`**: Date utility function tests
- **`tests/test_jira_client_json_parsing.py`**: JSON parsing error handling tests
- **`tests/test_jira_client_filter.py`**: Filter ID handling tests
- **`tests/test_history_fetcher.py`**: History fetcher module tests

### Scripts
- **`start_backend.sh`**: Start Flask backend server (port 8473)
- **`start_frontend.sh`**: Start frontend HTTP server (port 6291)
- **`start_all.sh`**: Start both servers concurrently
- **`start_with_tests.sh`**: Run tests then start servers with self-healing
- **`run_tests.sh`**: Run test suite with pytest
- **`kill_servers.sh`**: Kill processes on ports 8473 and 6291
- **`restart.sh`**: Restart servers (automatically runs tests first)
- **`uber.sh`**: Unified control script (start/stop/restart/status/test)

### Documentation
- **`README.md`**: Main project documentation
- **`CURSOR_PROMPT.md`**: Cursor-friendly development prompt with all requirements
- **`TEST_PLAN.md`**: Comprehensive test plan with test cases and known issues
- **`PROJECT_REQUIREMENTS.md`**: Detailed project requirements and user stories
- **`PROJECT_STRUCTURE.md`**: This file - directory structure overview

