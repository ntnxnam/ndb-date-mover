# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```bash
   cat > .env << EOF
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_PAT_TOKEN=your_personal_access_token_here
   EOF
   ```

3. **Update `.env` with your actual JIRA credentials:**
   - Replace `your-domain.atlassian.net` with your JIRA domain
   - Replace `your_personal_access_token_here` with your PAT token

## Running the Application

```bash
python3 app.py
```

Then open your browser to: `http://localhost:6291`

Click the "Test JIRA Connection" button to verify your connection.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Getting Your JIRA PAT Token

1. Go to your JIRA instance
2. Navigate to: **Account Settings** → **Security** → **API tokens**
3. Create a new API token
4. Copy the token to your `.env` file as `JIRA_PAT_TOKEN`

## Troubleshooting

### "JIRA credentials not configured"
- Make sure your `.env` file exists in the project root
- Check that `JIRA_URL` and `JIRA_PAT_TOKEN` are set correctly
- Ensure there are no extra spaces or quotes in the `.env` file

### "Authentication failed"
- Verify your PAT token is correct and hasn't expired
- Check that the token has the necessary permissions

### "Connection timeout"
- Check your internet connection
- Verify the JIRA URL is correct
- Check if your JIRA instance is accessible

