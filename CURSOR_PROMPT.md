# Cursor-Friendly Development Prompt

## Project: JIRA Date Tracking & Slip Analysis Tool

Build a web application that helps Engineering Program Managers track JIRA project date movements and calculate calendar week slips.

### Core Functionality

1. **JQL Query Interface**
   - Accept JQL queries from users (including nested filters like `filter=12345`)
   - Validate JQL syntax before execution
   - Execute queries against JIRA API and return structured table data

2. **Custom Field Configuration**
   - Create a JSON configuration file (`config/fields.json`) where users specify:
     - Custom field IDs to display
     - Which date fields to track history for
     - Column display order
   - Load and validate configuration at startup

3. **Dynamic Field Display Names**
   - Fetch custom field metadata from JIRA API (`/rest/api/3/field`)
   - Map field IDs to display names automatically
   - Use display names throughout UI (table headers, etc.)
   - Cache metadata to reduce API calls

4. **Date History Tracking**
   - For date fields flagged in config, fetch change history from JIRA changelog
   - Display current date prominently
   - Show all historical dates with CSS strike-through
   - Format: `mm/dd/yyyy` (e.g., `12/25/2024`)
   - Example display: `12/25/2024 ~~11/15/2024~~ ~~10/01/2024~~`

5. **Calendar Week Slip Calculation**
   - Calculate difference between original date (first in history) and current date
   - Display in calendar weeks (e.g., "+3 weeks", "-1 week")
   - Show prominently in bold
   - Color code: red for delays, green for ahead, gray for no change

6. **Self-Healing JIRA Connection**
   - Reuse existing connections when possible
   - Implement exponential backoff retry logic (max 3 attempts)
   - Handle timeouts gracefully (connection: 10s, read: 30s, request: 60s)
   - Detect and recover from connection failures automatically
   - Show connection status indicator in UI

7. **Error Handling**
   - Display clear, user-friendly error messages
   - Provide actionable guidance (what to do to fix)
   - Show error context (which operation failed)
   - Use visual indicators (icons, colors)

### UI Requirements

**Design:**
- Minimal grayscale design (lightweight, professional)
- Left sidebar navigation (Home, Query Builder, Configuration, Reports)
- Tabs for switching between data views
- Breadcrumbs showing navigation path (Home > Query Builder > Results)
- Top navigation bar with app title

**Components:**
- JQL input form with validation
- Sortable, filterable data table
- Date display with strike-through for history
- Week slip indicators (bold, color-coded)
- Connection status indicator
- Error alerts/notifications

### Technical Stack

**Backend:**
- Extend existing Flask API (`backend/app.py`)
- Extend existing JIRA client (`backend/jira_client.py`)
- Add endpoints:
  - `POST /api/query` - Execute JQL
  - `GET /api/fields` - Get field metadata
  - `GET /api/issue/{id}/history` - Get changelog
- Configuration loader for `config/fields.json`

**Frontend:**
- Extend existing frontend (`frontend/`)
- Add routing for multiple pages
- Build table component with sorting/filtering
- Date formatting utilities
- Error boundary components

### Configuration File Example

```json
{
  "custom_fields": [
    {
      "id": "customfield_12345",
      "type": "date",
      "track_history": true
    }
  ],
  "display_columns": [
    "key",
    "summary",
    "status",
    "customfield_12345"
  ]
}
```

### Implementation Priority

1. **Phase 1**: JQL input, basic table, config loading, field names
   - **Tests Required**: JQL validation, config loading, field metadata fetching
   - **Test Plan**: Document test scenarios for query execution and field display

2. **Phase 2**: Date history tracking, week slip calculation
   - **Tests Required**: Changelog parsing, date history extraction, week calculation
   - **Test Plan**: Document test cases for date tracking and slip calculation

3. **Phase 3**: UI navigation, tabs, breadcrumbs, grayscale design
   - **Tests Required**: Frontend routing, component rendering, user interactions
   - **Test Plan**: Document UI test scenarios and user flows

4. **Phase 4**: Self-healing connection, timeout handling, error display
   - **Tests Required**: Retry logic, connection recovery, error handling
   - **Test Plan**: Document resilience test scenarios

**For Each Phase:**
- Write tests alongside feature implementation
- Update test plan document with new scenarios
- Ensure test coverage meets 90% minimum
- Run full test suite before marking phase complete

### Success Criteria

- ✅ JQL queries (including filters) work correctly
- ✅ Custom field display names are fetched and shown
- ✅ Date history appears with strike-through
- ✅ Week slips are calculated accurately and displayed prominently
- ✅ Connection issues are handled gracefully
- ✅ Error messages are clear and helpful
- ✅ UI is clean, minimal, and navigable
- ✅ **All tests pass (unit, integration, E2E)**
- ✅ **Test coverage ≥ 90% for all new code**
- ✅ **Test plans updated and documented**
- ✅ **Tests run automatically on restart**

### Testing Requirements

**Test Coverage:**
- Minimum 90% code coverage for all new code
- Unit tests for all business logic functions
- Integration tests for API endpoints
- End-to-end tests for critical user flows
- Test plans must be updated for each feature

**Test Categories:**

1. **Unit Tests**
   - JQL query parsing and validation
   - Date calculation functions (week slip calculation)
   - Configuration file loading and validation
   - Field metadata fetching and caching
   - Date history parsing from changelog
   - Error handling and retry logic

2. **Integration Tests**
   - JIRA API connection and authentication
   - JQL query execution with various formats
   - Field metadata retrieval
   - Changelog fetching for date history
   - Self-healing connection retry mechanisms
   - Configuration file loading

3. **API Endpoint Tests**
   - `POST /api/query` - Test with valid/invalid JQL
   - `GET /api/fields` - Test field metadata retrieval
   - `GET /api/issue/{id}/history` - Test changelog retrieval
   - Error handling for all endpoints
   - Authentication and authorization

4. **Frontend Tests**
   - JQL input validation
   - Table rendering with data
   - Date formatting and strike-through display
   - Week slip calculation display
   - Error message display
   - Navigation and routing

5. **End-to-End Tests**
   - Complete flow: JQL input → query execution → table display
   - Date history tracking flow
   - Week slip calculation flow
   - Error handling flow
   - Connection recovery flow

**Test Plan Updates:**
- Create/update test plan document for each feature
- Document test scenarios and expected results
- Include edge cases and error conditions
- Update test plans when features change
- Maintain test coverage reports

**Test Execution:**
- All tests must pass before code merge
- Run tests automatically on server restart (via `./uber.sh restart`)
- Continuous integration: tests run on every commit
- Test reports generated with coverage metrics

**Test Data:**
- Use mock JIRA responses for unit tests
- Use test fixtures for consistent test data
- Mock external dependencies (JIRA API)
- Test with various JQL query formats
- Test with different date field configurations

### Code Guidelines

- Use existing `jira_client.py` as base, extend with new methods
- Follow existing code patterns and structure
- Add comprehensive logging
- Write unit tests for ALL functions (not just critical ones)
- Maintain separation between backend API and frontend UI
- Document API endpoints with examples
- **Write tests FIRST (TDD approach) or immediately after implementation**
- **Update test plans in documentation for each feature**
- **Ensure all tests pass before committing code**

