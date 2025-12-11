# Cursor-Friendly Development Prompt

## Project: JIRA Date Tracking & Slip Analysis Tool

Build a web application that helps Engineering Program Managers track JIRA project date movements and calculate calendar week slips.

### Core Functionality

1. **JQL Query Interface**
   - Accept JQL queries from users (including nested filters like `filter=12345`)
   - Validate JQL syntax before execution
   - Execute queries against JIRA API and return structured table data
   - **Filter ID handling**: Convert `filter=12345` to `filter = 12345` JQL format
   - **Filter validation**: Validate filter ID is numeric before API call
   - **HTML response detection**: Detect when JIRA returns HTML (auth/permission issues) and provide clear guidance

2. **Custom Field Configuration**
   - Create a JSON configuration file (`config/fields.json`) where users specify:
     - Custom field IDs to display
     - Which date fields to track history for
     - Column display order
   - Load and validate configuration at startup

3. **Dynamic Field Display Names**
   - Fetch custom field metadata from JIRA API (`/rest/api/2/field`)
   - Map field IDs to display names automatically
   - Use display names throughout UI (table headers, etc.)
   - Cache metadata to reduce API calls

4. **Date History Tracking**
   - **JIRA API v2 Changelog Format**: Uses `expand=changelog` parameter (not `/changelog` endpoint)
   - **Response Structure**: Handles `data['changelog']['histories']` format
   - **Field ID Resolution**: Resolves field IDs from field metadata when `fieldId` is missing in changelog items
   - **Field ID Normalization**: Converts numeric IDs (e.g., 11067) to `customfield_` format (e.g., `customfield_11067`)
   - **Field Matching**: Matches by normalized ID, original ID, numeric ID, or resolved ID
   - For date fields flagged in config, fetch change history from JIRA changelog
   - Display current date prominently
   - Show all historical dates with CSS strike-through
   - **Internal format**: Use JIRA-friendly formats (ISO 8601) for all internal processing
   - **Display format**: Always display dates as `mm/dd/yyyy` (e.g., `12/25/2024`)
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
   - **Critical**: Always check `Content-Type` header before parsing JSON responses
   - Handle non-JSON responses gracefully (HTML error pages, plain text, etc.)
   - Never crash on JSON parsing errors - provide helpful error messages instead

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
- ✅ Extended Flask API (`backend/app.py`) - API-only, no UI rendering
- ✅ Extended JIRA client (`backend/jira_client.py`) with new methods
- ✅ Created configuration loader (`backend/config_loader.py`)
- ✅ Created date utilities (`backend/date_utils.py`)
- ✅ Created history fetcher (`backend/history_fetcher.py`) - Fetches history for configured date fields
- ✅ Created AI summarizer (`backend/ai_summarizer.py`) - Executive-friendly text summarization
- ✅ Created shared utilities (`backend/utils.py`) - Error handling helpers
- ✅ Endpoints implemented:
  - `POST /api/query` - Execute JQL with date enrichment
  - `GET /api/fields` - Get field metadata
  - `GET /api/issue/{id}/history` - Get changelog
  - `GET /api/config` - Get configuration
  - `POST /api/test-connection` - Test connection
  - `GET /health` - Health check

**Frontend:**
- ✅ Created main application (`frontend/app.html`) with full UI
- ✅ Sidebar navigation with routing
- ✅ Table component with date history and week slips
- ✅ Date formatting utilities (always mm/dd/yyyy)
- ✅ Error handling with content-type checking
- ✅ Connection status indicator

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
  ],
  "date_format": "mm/dd/yyyy"
}
```

**Note on Date Formats:**
- **Internal processing**: All dates are handled in JIRA-friendly formats (ISO 8601) for API communication
- **Display format**: Dates are always displayed as `mm/dd/yyyy` regardless of configuration
- The `date_format` field in config is for documentation purposes only; display is always `mm/dd/yyyy`

### Implementation Priority

1. **Phase 1**: JQL input, basic table, config loading, field names ✅ COMPLETE
   - ✅ Tests: JQL validation, config loading, field metadata fetching
   - ✅ Test Plan: Documented test scenarios for query execution and field display
   - ✅ Files: `test_config_loader.py`, `test_jira_client_filter.py`

2. **Phase 2**: Date history tracking, week slip calculation ✅ COMPLETE
   - ✅ Tests: Changelog parsing, date history extraction, week calculation
   - ✅ Test Plan: Documented test cases for date tracking and slip calculation
   - ✅ Files: `test_date_utils.py`

3. **Phase 3**: UI navigation, tabs, breadcrumbs, grayscale design ✅ COMPLETE
   - ✅ Tests: Frontend routing, component rendering, user interactions
   - ✅ Test Plan: Documented UI test scenarios and user flows
   - ✅ Files: `frontend/app.html` with full UI implementation

4. **Phase 4**: Self-healing connection, timeout handling, error display ✅ COMPLETE
   - ✅ Tests: Retry logic, connection recovery, error handling, JSON parsing
   - ✅ Test Plan: Documented resilience test scenarios
   - ✅ Files: `test_jira_client_json_parsing.py`, enhanced `jira_client.py`

**For Each Phase:**
- ✅ Tests written alongside feature implementation
- ✅ Test plan document updated with new scenarios
- ✅ Test coverage meets 90% minimum for new code
- ✅ Full test suite runs automatically on restart

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
   - **JSON parsing error handling** (non-JSON responses from JIRA)
   - **Filter ID handling** (conversion, validation, HTML response detection)

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
   - **Non-JSON response handling** (HTML error pages, plain text responses)

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

**Environment Variable Handling in Tests:**
- **Unit tests MUST use `@patch.dict('os.environ', ...)` to mock environment variables**
- **DO NOT load from `.env` files in unit tests** - this breaks test isolation
- **Rationale**: Tests should be reproducible, isolated, and not require actual credentials
- **Pattern**: Mock `os.environ` since `load_dotenv()` loads `.env` into `os.environ`
- **Production code**: Still uses `.env` files via `load_dotenv()` - this is correct

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
- **Test Environment Variables**: Always use `@patch.dict('os.environ', ...)` in unit tests, never load from `.env` files
- **Code Quality**: Follow DRY principle, extract shared utilities, remove redundant code
- **Lightweight**: Keep code minimal, avoid bloat, remove unused files

