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

3. Add your JIRA credentials to `.env`:
```
JIRA_URL=https://your-domain.atlassian.net
JIRA_PAT_TOKEN=your_personal_access_token_here
```

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

## Project Structure

```
ndb-date-mover/
├── app.py                 # Flask application entry point
├── jira_client.py        # JIRA connection module
├── tests/                # Test files
│   └── test_jira_client.py
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in git)
└── README.md            # This file
```

