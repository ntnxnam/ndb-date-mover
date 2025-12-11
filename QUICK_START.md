# Quick Start Guide - Separated Backend & Frontend

## 🚀 Start Everything (Easiest Way)

```bash
./start_all.sh
```

Then open: **http://localhost:6291**

## 📋 Step-by-Step

### 1. Install Dependencies (First Time Only)

```bash
pip install -r requirements.txt
```

### 2. Configure JIRA Credentials

Edit `.env` file:
```
JIRA_URL=https://jira.nutanix.com
JIRA_PAT_TOKEN=your_token_here
```

### 3. Start Servers

**Option A: Both at once**
```bash
./start_all.sh
```

**Option B: Separately**

Terminal 1:
```bash
./start_backend.sh
```

Terminal 2:
```bash
./start_frontend.sh
```

### 4. Test Connection

1. Open browser: **http://localhost:6291**
2. Click **"Test JIRA Connection"** button
3. See results!

## 🔍 Verify Servers Are Running

- **Backend Health Check**: http://localhost:8473/health
- **Frontend**: http://localhost:6291

## 🛑 Stop Servers

Press `Ctrl+C` in the terminal(s) running the servers.

## 📁 Project Structure

```
backend/     → Flask API (Port 8473)
frontend/    → Web UI (Port 6291)
tests/       → Unit tests
```

## ❓ Troubleshooting

**Backend won't start?**
- Check port 8473 is free: `lsof -i :8473`
- Verify `.env` file exists

**Frontend can't connect?**
- Make sure backend is running first
- Check browser console for errors

**Connection test fails?**
- Verify JIRA credentials in `.env`
- Check token hasn't expired

