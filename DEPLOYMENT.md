# Deployment Guide

This guide explains how to deploy and run the separated backend and frontend servers.

## Architecture

```
┌─────────────────┐         HTTP Request          ┌─────────────────┐
│                 │ ────────────────────────────> │                 │
│  Frontend       │                                │   Backend       │
│  (Port 6291)    │ <──────────────────────────── │   (Port 8473)   │
│                 │      JSON Response            │                 │
└─────────────────┘                                └─────────────────┘
```

- **Frontend**: Serves static HTML/JS files on port 6291 (unusual port to avoid conflicts)
- **Backend**: Flask API server on port 8473 (unusual port to avoid conflicts) with CORS enabled

## Quick Start

### Option 1: Start Both Servers Together (Recommended)

```bash
./start_all.sh
```

This will start both backend and frontend servers simultaneously.

### Option 2: Start Servers Separately

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```

## Manual Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in project root:
```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_PAT_TOKEN=your_personal_access_token_here
```

### 3. Start Backend Server

```bash
cd backend
python3 app.py
```

Backend will run on: `http://localhost:8473`

### 4. Start Frontend Server

```bash
cd frontend
python3 server.py
```

Frontend will run on: `http://localhost:6291`

## Access the Application

1. Open your browser and navigate to: `http://localhost:6291`
2. Click the "Test JIRA Connection" button
3. The frontend will make a request to the backend API at `http://localhost:8473/api/test-connection`

## API Endpoints

### Backend API (Port 8473)

- `POST /api/test-connection` - Test JIRA connection
- `GET /health` - Health check endpoint

### Frontend (Port 6291)

- `GET /` - Main application page
- `GET /index.html` - Same as above

## Environment Variables

### Backend
- `JIRA_URL` - JIRA instance URL (required)
- `JIRA_PAT_TOKEN` - Personal Access Token (required)
- `SECRET_KEY` - Flask secret key (optional, has default)

### Frontend
- `FRONTEND_PORT` - Port for frontend server (default: 6291)
- `BACKEND_PORT` - Port for backend server (default: 8473)
- `BACKEND_API_URL` - Backend API URL (can be set in HTML, default: http://localhost:8473)

## Production Deployment

### Backend (Flask)

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:8473 app:app
```

### Frontend

For production, you can:
1. Use a production web server (Nginx, Apache)
2. Deploy to a static hosting service (Netlify, Vercel, etc.)
3. Use a containerized solution (Docker)

### Docker Deployment (Optional)

Create `Dockerfile.backend`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./backend/
COPY .env .env
EXPOSE 8473
CMD ["python", "backend/app.py"]
```

Create `Dockerfile.frontend`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY frontend/ ./frontend/
EXPOSE 6291
CMD ["python", "frontend/server.py"]
```

## Troubleshooting

### Backend not starting
- Check if port 8473 is already in use
- Verify `.env` file exists and has correct credentials
- Check Python dependencies are installed

### Frontend can't connect to backend
- Verify backend is running on port 8473
- Check CORS is enabled in backend (it should be)
- Check browser console for errors
- Verify firewall settings

### Connection test fails
- Verify JIRA credentials in `.env` file
- Check JIRA URL format (should be `https://domain.atlassian.net`)
- Verify PAT token is valid and not expired
- Check network connectivity to JIRA instance

## Port Configuration

To change ports:

**Backend:** Edit `backend/app.py`:
```python
app.run(debug=True, host="0.0.0.0", port=8474)  # Change port here
```

**Frontend:** Set environment variable:
```bash
export FRONTEND_PORT=6292
python3 frontend/server.py
```

Or edit `frontend/index.html` to update `BACKEND_API_URL` if backend port changes.

