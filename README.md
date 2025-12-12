# NDB Date Mover

A Python application for connecting to JIRA using Personal Access Token (PAT) authentication.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root:
```bash
touch .env
```

3. Add your JIRA credentials and AI API key to `.env`:
```
JIRA_URL=https://your-domain.atlassian.net
JIRA_PAT_TOKEN=your_personal_access_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional: for Claude API
# OR
OPENAI_API_KEY=your_openai_api_key_here  # Optional: for OpenAI API fallback
```

**Note:** AI API keys are optional but recommended for intelligent summarization:
- `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com/ (preferred)
- `OPENAI_API_KEY`: Get from https://platform.openai.com/ (fallback option)
- If neither is provided, the app will fall back to rule-based summarization.

**Note**: The `.env` file is already in `.gitignore` and will not be committed to git.

## Running the Application

### Quick Start (Recommended)

**Option 1: Use the uber script (recommended):**
```bash
./uber.sh restart    # Run tests, then kill existing and restart everything
./uber.sh test       # Run tests and start servers with self-healing
./uber.sh start      # Start servers (no tests)
./uber.sh stop       # Stop all servers
./uber.sh status     # Check server status
```

**Note:** `restart` and `test` commands automatically run tests before starting servers.

**Option 2: Start everything:**
```bash
./start_all.sh
```

Then navigate to `http://localhost:6291` in your browser.

**Note:** The frontend will automatically redirect to `app.html` which contains the full JIRA Date Tracker interface with:
- Sidebar navigation
- JQL Query Builder
- Date history tracking
- Week slip calculations
- Configuration management
- Export functionality (CSV, Email)

### Separate Servers

**Backend (Terminal 1):**
```bash
./start_backend.sh
```

**Frontend (Terminal 2):**
```bash
./start_frontend.sh
```

### Stop Servers

```bash
./kill_servers.sh    # Kill processes on ports 8473 and 6291
./uber.sh stop       # Alternative: use uber script
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Testing

Run tests with:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Recent Updates

- ✅ **Email Export Functionality**: Send formatted HTML emails with CSV attachments
  - HTML email body matching UI table display
  - SMTP configuration via `config/smtp.json`
  - Timezone support (default: IST/Asia/Kolkata)
  - Always CC namratha.singh@nutanix.com
  - Subject format: "TPM Bot: Project Dates and Effort Estimate - {date}"
- ✅ JIRA API v2 changelog compliance (uses `expand=changelog`)
- ✅ HistoryFetcher module for fetching date history
- ✅ Field ID normalization and resolution
- ✅ Configurable table columns (only shows configured fields)
- ✅ Added fixVersions field support
- ✅ Added Risk Indicator field (customfield_23560)
- ✅ Added Status Update field with AI summarization (customfield_23073)
- ✅ AI summarization module for executive-friendly text summaries
- ✅ Fixed Content-Type header logic in after_request
- ✅ Fixed pytest coverage configuration paths
- ✅ Fixed config file invalid control character
- ✅ Comprehensive test coverage

## Project Structure

```
ndb-date-mover/
├── backend/              # Backend API server
│   ├── app.py           # Flask application
│   ├── jira_client.py   # JIRA connection module
│   ├── config_loader.py # Configuration loader
│   ├── date_utils.py    # Date utilities
│   └── history_fetcher.py # History fetcher module
├── frontend/            # Frontend web server
│   ├── app.html         # Main application UI
│   └── server.py        # Static file server
├── config/              # Configuration files
│   ├── fields.json      # Field configuration
│   └── smtp.json        # SMTP email configuration
├── tests/               # Test files
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
└── README.md           # This file
```

