# JIRA Date Tracking Application - Requirements

## Project Overview
A web application for tracking and visualizing JIRA project date movements. The tool helps Engineering Program Managers monitor how many times project dates have changed and calculate calendar week slips.

## Core Features

### 1. JQL Query Input
- **Accept JQL queries** from users via UI input field
- **Support nested filters** in format: `filter=xxxxxxx` (where xxxxxxx is a filter ID)
- **Support filter with additional clauses**: `filter=12345 ORDER BY fixVersion ASC` or `filter=12345 AND status = Open`
- **Filter parsing priority**: ORDER BY detected first, then AND/OR clauses
- **Validate JQL syntax** before submission
- **Store recent queries** for quick access

### 2. JIRA Data Fetching
- **Execute JQL queries** against JIRA API
- **Return structured table data** with all issue fields
- **Handle pagination** for large result sets
- **Cache results** appropriately to reduce API calls

### 3. Custom Field Configuration
- **Configuration file format**: JSON or YAML (e.g., `config/fields.json`)
- **Structure**:
  ```json
  {
    "custom_fields": [
      {
        "id": "customfield_12345",
        "name": "Target Release Date",
        "type": "date",
        "track_history": true
      },
      {
        "id": "customfield_67890",
        "name": "Start Date",
        "type": "date",
        "track_history": false
      }
    ],
    "display_columns": [
      "key",
      "summary",
      "status",
      "customfield_12345",
      "customfield_67890"
    ]
  }
  ```
- **Load configuration** at application startup
- **Validate configuration** format and field IDs

### 4. Custom Field Display Names
- **Fetch field metadata** from JIRA API (`/rest/api/3/field`)
- **Map custom field IDs** to their display names
- **Use display names** throughout the UI (table headers, filters, etc.)
- **Cache field metadata** to avoid repeated API calls
- **Fallback to field ID** if display name cannot be fetched

### 5. User Interface Requirements

#### Design Principles
- **Minimal grayscale design** - clean, professional, lightweight
- **Lightweight UI** - fast loading, minimal dependencies
- **Responsive layout** - works on different screen sizes

#### Layout Structure
- **Left sidebar navigation**:
  - Home/Dashboard
  - Query Builder
  - Configuration
  - History/Reports
- **Main content area** with tabs for different views
- **Breadcrumbs** showing current location (e.g., Home > Query Builder > Results)
- **Top navigation bar** with app title and user info

#### UI Components
- **Tabs**: Use for switching between different data views
- **Breadcrumbs**: Show navigation path
- **Data table**: Sortable, filterable columns
- **Forms**: Clean input fields for JQL and configuration
- **Status indicators**: Visual feedback for connection status

### 6. Table Display
- **Render table** with columns specified in configuration file
- **Use custom field display names** as column headers
- **Support sorting** by any column
- **Support filtering** by column values
- **Pagination** for large datasets
- **Export functionality** (CSV, Excel)

### 7. Date Field History Tracking

#### Requirements
- **Accept flag per date field** in configuration (e.g., `track_history: true`)
- **Fetch change history** from JIRA API (`/rest/api/3/issue/{issueId}/changelog`)
- **Track all date changes** for flagged fields
- **Display current date** prominently
- **Show historical dates** with strike-through formatting in reverse chronological order (newest first)
- **Format**: `dd/mmm/yyyy` (e.g., `15/Jan/2026`)
- **Current date exclusion**: Current date must NOT appear in struck-out history (CRITICAL)
- **Date comparison**: Uses 3-method comparison (normalized ISO, string, formatted) to handle different formats
- **Format support**: Parser supports dd/mmm/yyyy and dd/mmm/yy formats for accurate comparison
- **Edge cases**: Handles same date in different formats (e.g., 13/Jun/2025 vs 13/Jun/25) correctly
- **Change count**: Displays total number of date changes (including reverts: A->B->A = 3 changes)
- **Date difference**: Calculates and displays difference from first date to current date:
  - If difference < 7 days: Shows as "X days" (e.g., "4 days")
  - If difference >= 7 days: Shows as "X weeks" with proper rounding (e.g., "1.5 weeks", "2 weeks")
- **Visual example**:
  ```
  Target Release Date: 12/25/2024
  ~~11/15/2024~~ ~~10/01/2024~~ ~~09/15/2024~~
  ```

#### Implementation
- Query JIRA changelog for each issue
- Filter changes for specific custom field IDs
- Parse date values from change history
- Sort dates chronologically (oldest to newest)
- Apply CSS strike-through styling

### 8. Calendar Week Slip Calculation

#### Requirements
- **Calculate week slips** for each date field that has history
- **Display prominently** (bold, highlighted)
- **Formula**: 
  - Original date (first date in history) vs Current date
  - Calculate difference in calendar weeks
  - Account for partial weeks appropriately

#### Display Format
- **Bold text**: "**+3 weeks**" or "**-1 week**"
- **Color coding**: 
  - Red for positive slips (delays)
  - Green for negative slips (ahead of schedule)
  - Gray for no change
- **Tooltip**: Show original date and current date

### 9. Self-Healing JIRA Connection

#### Connection Management
- **Reuse existing connections** when possible (connection pooling)
- **Detect connection failures** (timeout, network error, auth failure)
- **Automatic retry logic**:
  - Exponential backoff for transient failures
  - Max retry attempts (e.g., 3 retries)
  - Different strategies for different error types
- **Connection health monitoring**:
  - Periodic health checks
  - Detect stale connections
  - Refresh tokens if needed

#### Timeout Handling
- **Configurable timeouts**:
  - Connection timeout: 10 seconds
  - Read timeout: 30 seconds
  - Request timeout: 60 seconds
- **Graceful degradation**:
  - Show partial results if some requests fail
  - Queue failed requests for retry
  - Display connection status indicator

#### Error Recovery
- **Token refresh** if authentication fails
- **Reconnect** on network errors
- **Cache results** to serve stale data if connection fails
- **User notification** of connection issues

### 10. Error Handling & User Communication

#### Error Types to Handle
- **JQL syntax errors**: Invalid query format
- **JIRA API errors**: 400, 401, 403, 404, 500
- **Network errors**: Timeout, connection refused
- **Configuration errors**: Invalid field IDs, missing config
- **Data parsing errors**: Unexpected response format

#### Error Display Requirements
- **Clear, user-friendly messages** (no technical jargon)
- **Actionable guidance**: What the user should do
- **Error context**: Which operation failed, what data was involved
- **Recovery suggestions**: How to fix the issue
- **Visual indicators**: Icons, colors, alerts

#### Error Message Examples
- ❌ "Invalid JQL query. Please check your syntax. Error: 'project' is required"
- ⚠️ "Connection to JIRA timed out. Retrying... (Attempt 2/3)"
- 🔒 "Authentication failed. Please check your JIRA token in .env file"
- 📋 "Custom field 'customfield_12345' not found. Please verify field ID in configuration"

## Technical Architecture

### Backend (Flask API)
- **Endpoints**:
  - `POST /api/query` - Execute JQL query with date enrichment
  - `GET /api/fields` - Fetch field metadata
  - `GET /api/issue/{id}/history` - Get issue change history
  - `GET /api/config` - Get current configuration
  - `POST /api/test-connection` - Test JIRA connection
  - `GET /health` - Connection health check
- **JIRA Client**: Extended `backend/jira_client.py` with:
  - `execute_jql()` - Execute JQL queries (supports filter IDs)
  - `get_field_metadata()` - Fetch field display names
  - `get_issue_changelog()` - Fetch change history
  - Self-healing retry logic with exponential backoff
- **Configuration loader**: `backend/config_loader.py` - Load and validate `config/fields.json`
- **Date utilities**: `backend/date_utils.py` - Date formatting and week slip calculations
- **Error handling**: HTML response detection, JSON parsing error handling

### Frontend (Vanilla JavaScript)
- **Single-page application**: `frontend/app.html` with client-side routing
- **Navigation**: Sidebar navigation (Home, Query Builder, Configuration, Reports)
- **Breadcrumbs**: Shows navigation path (Home > Query Builder > Results)
- **Tabs**: Switch between table view and raw data view
- **API client**: Handles all backend communication with error handling
- **Table component**: Displays query results with date history and week slips
- **Date formatting**: Formats dates as mm/dd/yyyy with strike-through for history
- **Error handling**: Content-type checking, JSON parsing error handling, user-friendly messages
- **Connection status**: Real-time backend connection indicator

### Data Flow
1. User enters JQL query
2. Frontend sends query to backend
3. Backend validates query and executes against JIRA
4. Backend fetches custom field metadata
5. Backend fetches change history for date fields (if flagged)
6. Backend calculates week slips
7. Backend returns formatted data
8. Frontend displays table with dates, history, and slips

## Configuration File Structure

**Location**: `config/fields.json` (create from `config/fields.json.example`)

```json
{
  "custom_fields": [
    {
      "id": "customfield_11067",
      "type": "date",
      "track_history": true,
      "display_name": "Code Complete Date"
    },
    {
      "id": "customfield_35863",
      "type": "date",
      "track_history": true,
      "display_name": "Commit Gate Ready Estimation Date"
    }
  ],
  "display_columns": [
    "key",
    "summary",
    "status",
    "assignee",
    "resolution",
    "customfield_11067",
    "customfield_35863"
  ],
  "date_format": "mm/dd/yyyy"
}
```

**Note on Date Formats:**
- **Internal processing**: All dates handled in JIRA-friendly formats (ISO 8601)
- **Display format**: Always displayed as `mm/dd/yyyy` regardless of config
- The `date_format` field is for documentation purposes only

## User Stories

### As an Engineering Program Manager:
1. **I want to** enter a JQL query to see all issues in my project
2. **I want to** see which dates have changed and how many times
3. **I want to** quickly identify which dates have slipped by how many weeks
4. **I want to** understand connection issues and know when data is stale
5. **I want to** configure which fields to track without code changes
6. **I want to** navigate easily between different views of the data

## Success Criteria

- ✅ JQL queries (including filters) execute successfully
- ✅ Custom field display names are fetched and displayed correctly
- ✅ Date history is tracked and displayed with strike-through
- ✅ Week slip calculations are accurate and prominently displayed
- ✅ Connection issues are handled gracefully with automatic recovery
- ✅ Error messages are clear and actionable
- ✅ UI is clean, minimal, and easy to navigate
- ✅ Application performs well with large datasets (1000+ issues)

## Implementation Phases

### Phase 1: Core Functionality ✅ COMPLETE
- ✅ JQL query input and execution (supports filter IDs)
- ✅ Basic table display with sortable columns
- ✅ Configuration file loading and validation
- ✅ Custom field display name fetching
- ✅ Filter ID handling with validation

### Phase 2: Date Tracking ✅ COMPLETE
- ✅ Change history fetching from changelog
- ✅ Date formatting (mm/dd/yyyy) with strike-through display
- ✅ Week slip calculation with color coding

### Phase 3: UI/UX ✅ COMPLETE
- ✅ Sidebar navigation (Home, Query Builder, Configuration, Reports)
- ✅ Tabs (Table View, Raw Data)
- ✅ Breadcrumbs showing navigation path
- ✅ Grayscale minimal design
- ✅ Error display improvements with actionable guidance

### Phase 4: Resilience ✅ COMPLETE
- ✅ Self-healing connection logic with exponential backoff
- ✅ Timeout handling (connection: 10s, read: 30s, request: 60s)
- ✅ Retry mechanisms (max 3 attempts)
- ✅ Connection status indicators in UI
- ✅ HTML response detection for auth/permission issues
- ✅ JSON parsing error handling

## Technical Notes

- **Use existing JIRA client** from `backend/jira_client.py` as base ✅
- **Extend with new methods** for changelog and field metadata ✅
- **Maintain separation** between backend API and frontend UI ✅
- **Follow existing code patterns** and conventions ✅
- **Add comprehensive logging** for debugging ✅
- **Write unit tests** for ALL functions (not just critical) ✅
- **Document API endpoints** with examples ✅

## Implementation Status

### Completed Features
- ✅ JQL query execution with filter ID support
- ✅ Configuration file loading and validation
- ✅ Custom field display name fetching
- ✅ Date history tracking with strike-through
- ✅ Week slip calculation and display
- ✅ Self-healing connection with retry logic
- ✅ HTML response detection and error handling
- ✅ JSON parsing error handling
- ✅ Sidebar navigation and multi-page UI
- ✅ Tabs and breadcrumbs
- ✅ Connection status indicator
- ✅ Comprehensive test suite (60+ tests)
- ✅ fixVersions field support
- ✅ Risk Indicator field (customfield_23560)
- ✅ Status Update field with AI summarization (customfield_23073)
- ✅ AI summarization module for executive-friendly text

### Recent Features Added (2024)

**New Fields:**
- ✅ **fixVersions** - Standard JIRA field for version tracking
- ✅ **customfield_23560** - Risk Indicator field
- ✅ **customfield_23073** - Status Update field with AI summarization

**AI Summarization:**
- ✅ Created `backend/ai_summarizer.py` module
- ✅ Executive-friendly text summarization (max 200 characters)
- ✅ Frontend displays summary with expandable full text
- ✅ Configurable via `ai_summarize` and `exec_friendly` flags

### Recent Bug Fixes

### Bug Fix 1: Content-Type Header Logic (backend/app.py)
- **Issue**: Contradictory logic in `after_request` function
- **Fix**: Removed redundant conditional block, single correct logic
- **Status**: ✅ Fixed
- **Commit**: cb028bb

### Bug Fix 2: Pytest Coverage Configuration (pytest.ini)
- **Issue**: Coverage paths pointed to wrong modules
- **Fix**: Updated to `backend.jira_client` and `backend.app`
- **Status**: ✅ Fixed
- **Commit**: 3873a1f

### Bug Fix 3: Config File Invalid Control Character
- **Issue**: Tab character in config/fields.json causing JSON parsing errors
- **Fix**: Removed invalid control character
- **Status**: ✅ Fixed
- **Commit**: 9bb8f3c

## Known Issues and Solutions
1. **JSON Parsing Errors**: Fixed with content-type checking before parsing
2. **Filter ID HTML Responses**: Fixed with HTML detection and specific error messages
3. **Test Environment Variables**: Documented - using `@patch.dict` is correct pattern

### Testing
- **Test Coverage**: 90%+ for new code
- **Test Execution**: Automatic on restart (`./uber.sh restart`)
- **Test Files**: 6 test modules covering all functionality
- **Test Plan**: Comprehensive documentation in `TEST_PLAN.md`


