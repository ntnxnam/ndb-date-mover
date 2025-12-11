# JIRA Date Tracking Application - Requirements

## Project Overview
A web application for tracking and visualizing JIRA project date movements. The tool helps Engineering Program Managers monitor how many times project dates have changed and calculate calendar week slips.

## Core Features

### 1. JQL Query Input
- **Accept JQL queries** from users via UI input field
- **Support nested filters** in format: `filter=xxxxxxx` (where xxxxxxx is a filter ID)
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
- **Show historical dates** with strike-through formatting
- **Format**: `mm/dd/yyyy` (e.g., `12/25/2024`)
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
  - `POST /api/query` - Execute JQL query
  - `GET /api/fields` - Fetch field metadata
  - `GET /api/issue/{id}/history` - Get issue change history
  - `GET /api/health` - Connection health check
- **JIRA Client**: Extend existing `jira_client.py`
- **Configuration loader**: Load and validate config file
- **Caching layer**: Redis or in-memory cache for field metadata

### Frontend (React/Vue or Vanilla JS)
- **Routing**: Client-side routing for different pages
- **State management**: Store query results, configuration, UI state
- **API client**: Handle all backend communication
- **Table component**: Sortable, filterable data table
- **Date formatting**: Format dates consistently
- **Error boundaries**: Catch and display errors gracefully

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

```json
{
  "jira": {
    "base_url": "https://jira.nutanix.com",
    "timeout": 30,
    "retry_attempts": 3
  },
  "custom_fields": [
    {
      "id": "customfield_12345",
      "type": "date",
      "track_history": true,
      "display_name": "Target Release Date"
    }
  ],
  "display_columns": [
    "key",
    "summary",
    "status",
    "assignee",
    "customfield_12345"
  ],
  "date_format": "mm/dd/yyyy"
}
```

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

### Phase 1: Core Functionality
- JQL query input and execution
- Basic table display
- Configuration file loading
- Custom field display name fetching

### Phase 2: Date Tracking
- Change history fetching
- Date formatting and strike-through display
- Week slip calculation

### Phase 3: UI/UX
- Sidebar navigation
- Tabs and breadcrumbs
- Grayscale minimal design
- Error display improvements

### Phase 4: Resilience
- Self-healing connection logic
- Timeout handling
- Retry mechanisms
- Connection status indicators

## Technical Notes

- **Use existing JIRA client** from `backend/jira_client.py` as base
- **Extend with new methods** for changelog and field metadata
- **Maintain separation** between backend API and frontend UI
- **Follow existing code patterns** and conventions
- **Add comprehensive logging** for debugging
- **Write unit tests** for critical functions (JQL parsing, date calculations)
- **Document API endpoints** with examples

