# Test Plan - JIRA Date Tracking Application

## Overview

This document outlines the comprehensive test plan for the JIRA Date Tracking & Slip Analysis Tool. All features must be thoroughly tested before deployment.

## Test Execution

**Automatic Test Execution:**
- Tests run automatically on server restart: `./uber.sh restart`
- Tests run before starting: `./uber.sh test`
- Manual execution: `./run_tests.sh`

**Test Coverage Requirement:** Minimum 90% for all new code

---

## Phase 1: Core Functionality Tests

### 1.1 JQL Query Interface

#### Test Cases:
- ✅ **TC-1.1.1**: Valid JQL query execution
  - Input: `project = PROJ AND status = "In Progress"`
  - Expected: Returns list of issues
  - Test: Unit + Integration

- ✅ **TC-1.1.2**: Nested filter query
  - Input: `filter=12345`
  - Expected: Resolves filter and returns issues
  - Test: Unit + Integration

- ✅ **TC-1.1.3**: Invalid JQL syntax
  - Input: `project =` (incomplete)
  - Expected: Returns validation error
  - Test: Unit

- ✅ **TC-1.1.4**: Empty JQL query
  - Input: `""`
  - Expected: Returns validation error
  - Test: Unit

- ✅ **TC-1.1.5**: JQL with special characters
  - Input: `summary ~ "test & demo"`
  - Expected: Properly escaped and executed
  - Test: Integration

- ✅ **TC-1.1.6**: Non-JSON response from JIRA
  - Input: JIRA returns HTML error page instead of JSON
  - Expected: Graceful error handling, no JSON parsing crash, clear error message
  - Test: Integration
  - **Critical**: Must check content-type before parsing JSON

- ✅ **TC-1.1.7**: Filter ID handling
  - Input: `filter=165194`
  - Expected: Converts to `filter = 165194` JQL format
  - Test: Unit + Integration

- ✅ **TC-1.1.8**: Filter ID with HTML response (auth/permission issue)
  - Input: Filter ID that returns HTML (login page or error)
  - Expected: Clear error message about authentication/permissions
  - Test: Integration
  - **Critical**: Must detect HTML responses and provide actionable guidance

- ✅ **TC-1.1.9**: Invalid filter ID format
  - Input: `filter=abc123` (non-numeric)
  - Expected: Validation error before API call
  - Test: Unit

- ✅ **TC-1.1.10**: Filter with ORDER BY clause
  - Input: `filter=165194 order by fixVersion ASC`
  - Expected: Correctly parses filter ID and ORDER BY clause
  - Test: Unit + Integration
  - **Critical**: ORDER BY must be detected and separated from filter ID

- ✅ **TC-1.1.11**: Filter with AND clause
  - Input: `filter=165194 and status = Open`
  - Expected: Correctly parses filter ID and AND clause
  - Test: Unit + Integration

#### Test Plan Updates:
- Document all JQL query formats supported
- List edge cases and error scenarios
- Update when new JQL features added

---

### 1.2 Custom Field Configuration

#### Test Cases:
- ✅ **TC-1.2.1**: Valid configuration file loading
  - Input: Valid `config/fields.json`
  - Expected: Configuration loaded successfully
  - Test: Unit

- ✅ **TC-1.2.2**: Invalid JSON format
  - Input: Malformed JSON
  - Expected: Clear error message
  - Test: Unit

- ✅ **TC-1.2.3**: Missing required fields
  - Input: Config without `custom_fields`
  - Expected: Validation error
  - Test: Unit

- ✅ **TC-1.2.4**: Invalid custom field ID format
  - Input: `customfield_abc` (invalid)
  - Expected: Validation error
  - Test: Unit

- ✅ **TC-1.2.5**: Configuration with duplicate field IDs
  - Input: Same field ID twice
  - Expected: Deduplication or error
  - Test: Unit

#### Test Plan Updates:
- Document configuration schema
- List all validation rules
- Update when new config options added

---

### 1.3 Dynamic Field Display Names

#### Test Cases:
- ✅ **TC-1.3.1**: Fetch field metadata from JIRA
  - Input: Valid field ID
  - Expected: Returns display name
  - Test: Integration

- ✅ **TC-1.3.2**: Field ID not found in JIRA
  - Input: Invalid field ID
  - Expected: Fallback to field ID or error
  - Test: Integration

- ✅ **TC-1.3.3**: Metadata caching
  - Input: Multiple requests for same field
  - Expected: Cached result used (no duplicate API calls)
  - Test: Integration

- ✅ **TC-1.3.4**: Cache invalidation
  - Input: Cache timeout or manual refresh
  - Expected: Fresh data fetched
  - Test: Unit

- ✅ **TC-1.3.5**: Batch field metadata fetching
  - Input: Multiple field IDs
  - Expected: All metadata retrieved efficiently
  - Test: Integration

#### Test Plan Updates:
- Document caching strategy
- List cache invalidation scenarios
- Update when caching logic changes

---

## Phase 2: Date Tracking Tests

### 2.1 Date History Tracking

#### Test Cases:
- ✅ **TC-2.1.1**: Fetch changelog for issue
  - Input: Valid issue ID with date field changes
  - Expected: Returns all date change history
  - Test: Integration

- ✅ **TC-2.1.2**: Date field with no history
  - Input: Issue with date field never changed
  - Expected: Shows only current date
  - Test: Integration

- ✅ **TC-2.1.3**: Multiple date changes
  - Input: Issue with 5+ date changes
  - Expected: All dates displayed in chronological order
  - Test: Integration

- ✅ **TC-2.1.4**: Date format validation
  - Input: Various date formats from JIRA
  - Expected: All converted to `mm/dd/yyyy`
  - Test: Unit

- ✅ **TC-2.1.5**: Strike-through display
  - Input: Historical dates
  - Expected: CSS strike-through applied correctly
  - Test: Frontend

- ✅ **TC-2.1.6**: Current date exclusion from history (CRITICAL)
  - Input: Current date and history dates in various formats
  - Expected: Current date NEVER appears in struck-out history
  - Test: Unit + Integration (test_date_comparison_fix.py)
  - **Critical**: Must handle different date formats (ISO, dd/mmm/yyyy, dd/mmm/yy)
  - **Validation**: Same date in different formats (e.g., 13/Jun/2025 vs 13/Jun/25) must be excluded
  - **Edge Cases**: 
    - ISO format vs formatted string
    - Full year vs short year (2025 vs 25)
    - Already formatted dates in history
  - **Comparison Methods**: Uses 3-method comparison (normalized ISO, string, formatted)

- ✅ **TC-2.1.7**: Change count calculation
  - Input: Date field with multiple changes including reverts (A->B->A)
  - Expected: Change count = total number of changes (A->B->A = 3 changes)
  - Test: Unit (test_date_change_count.py)
  - **Critical**: Must count ALL changes, even when date reverts to previous value

- ✅ **TC-2.1.8**: Date difference from first to current
  - Input: First date in history and current date
  - Expected: Difference calculated and displayed using days/weeks format
  - Test: Unit (test_date_change_count.py)
  - **Validation**: < 7 days shows as "X days", >= 7 days shows as "X weeks" with proper rounding

- ✅ **TC-2.1.9**: Changelog API error handling
  - Input: Issue with no changelog access
  - Expected: Graceful error handling
  - Test: Integration

#### Test Plan Updates:
- Document date parsing logic
- List all date format edge cases
- Update when date display changes

---

### 2.2 Calendar Week Slip Calculation

#### Test Cases:
- ✅ **TC-2.2.1**: Positive week slip (delay)
  - Input: Original date: 01/01/2024, Current: 01/22/2024
  - Expected: "+3 weeks" displayed in red
  - Test: Unit

- ✅ **TC-2.2.2**: Negative week slip (ahead)
  - Input: Original date: 01/22/2024, Current: 01/01/2024
  - Expected: "-3 weeks" displayed in green
  - Test: Unit

- ✅ **TC-2.2.3**: No slip (same date)
  - Input: Original date: 01/01/2024, Current: 01/01/2024
  - Expected: "0 weeks" displayed in gray
  - Test: Unit

- ✅ **TC-2.2.4**: Partial week calculation
  - Input: 4 days difference
  - Expected: Rounds appropriately (0 or 1 week)
  - Test: Unit

- ✅ **TC-2.2.5**: Week slip with no history
  - Input: Date field never changed
  - Expected: "0 weeks" or "N/A"
  - Test: Unit

- ✅ **TC-2.2.6**: Week slip display formatting
  - Input: Various slip values
  - Expected: Bold, color-coded display
  - Test: Frontend

#### Test Plan Updates:
- Document week calculation algorithm
- List edge cases (leap years, month boundaries)
- Update when calculation logic changes

---

## Phase 3: UI/UX Tests

### 3.1 Navigation and Layout

#### Test Cases:
- ✅ **TC-3.1.1**: Sidebar navigation
  - Input: Click navigation items
  - Expected: Correct page loads
  - Test: Frontend E2E

- ✅ **TC-3.1.2**: Breadcrumb navigation
  - Input: Navigate through pages
  - Expected: Breadcrumbs update correctly
  - Test: Frontend

- ✅ **TC-3.1.3**: Tab switching
  - Input: Click different tabs
  - Expected: Content switches correctly
  - Test: Frontend

- ✅ **TC-3.1.4**: Responsive design
  - Input: Different screen sizes
  - Expected: Layout adapts properly
  - Test: Frontend

#### Test Plan Updates:
- Document navigation structure
- List all routes and pages
- Update when new pages added

---

### 3.2 Data Table

#### Test Cases:
- ✅ **TC-3.2.1**: Table rendering with data
  - Input: Query results from backend API
  - Expected: Table displays only configured columns from `display_columns`
  - Test: Frontend + Unit (test_frontend_rendering.py)
  - **Validation**: Only columns in `config/fields.json` display_columns are shown

- ✅ **TC-3.2.2**: Date field rendering
  - Input: Date field with history and week slip
  - Expected: 
    - Current date displayed in bold (dd/mmm/yyyy format)
    - Historical dates displayed struck-out in reverse chronological order (newest first)
    - Week slip displayed with color coding (red/green/gray)
  - Test: Frontend + Unit (test_frontend_rendering.py)
  - **Critical**: Current date must NOT appear in struck-out history

- ✅ **TC-3.2.3**: Date format validation
  - Input: Date values from JIRA API
  - Expected: All dates displayed as dd/mmm/yyyy (e.g., 15/Jan/2026)
  - Test: Unit (test_frontend_rendering.py, test_date_comparison_fix.py)
  - **Validation**: format_date() returns dd/mmm/yyyy format
  - **Critical**: format_date() must also parse already-formatted dates (dd/mmm/yyyy, dd/mmm/yy)

- ✅ **TC-3.2.4**: Risk Indicator color highlighting
  - Input: Risk Indicator field value (object, array, or string)
  - Expected: 
    - Value extracted correctly from object (value, name, displayName, label, id)
    - Handles arrays (extracts from first element)
    - Iterates through object properties to find string values
    - Extracts from JSON string if needed
    - Validates extracted text (not [object Object] or {})
    - Color badge applied (red/yellow/green) based on value
    - Case-insensitive matching
    - Fallback to '-' if no valid value found
  - Test: Frontend + Unit (test_frontend_rendering.py)
  - **Validation**: Object/array values properly extracted, colors correctly applied, no [object Object] display

- ✅ **TC-3.2.5**: AI Summary display
  - Input: Status Update field with AI summary
  - Expected:
    - AI summary displayed when `show_ai_summary` is true
    - Original text available in expandable "View full text"
    - Falls back to original if no summary available
  - Test: Frontend + Unit (test_frontend_rendering.py)

- ✅ **TC-3.2.6**: FixVersions array rendering
  - Input: fixVersions array from JIRA
  - Expected: Comma-separated list of version names
  - Test: Frontend + Unit (test_frontend_rendering.py)

- ✅ **TC-3.2.7**: Pagination
  - Input: Large dataset (100+ issues)
  - Expected: 
    - Correct page size selection (10, 25, 50, 100, 200)
    - Correct page navigation (Previous/Next)
    - Correct page number display
    - Correct "Showing X-Y of Z issues" message
  - Test: Frontend + Unit (test_frontend_rendering.py)

- ✅ **TC-3.2.8**: Empty table state
  - Input: No results from query
  - Expected: Appropriate empty state message
  - Test: Frontend

- ✅ **TC-3.2.9**: Object field value extraction
  - Input: Fields with object values (assignee, status, etc.)
  - Expected: displayName or name extracted correctly
  - Test: Frontend + Unit (test_frontend_rendering.py)

- ✅ **TC-3.2.10**: Date history reverse chronological order
  - Input: Date history array
  - Expected: History displayed newest first, oldest last
  - Test: Unit (test_frontend_rendering.py)
  - **Validation**: History array is reversed before display

#### Test Plan Updates:
- Document table features
- List all rendering validations
- Update when table features added
- **Frontend Rendering Tests**: See `tests/test_frontend_rendering.py`

---

## Phase 4: Resilience Tests

### 4.1 Self-Healing Connection

#### Test Cases:
- ✅ **TC-4.1.1**: Connection timeout recovery
  - Input: Simulated timeout
  - Expected: Automatic retry with backoff
  - Test: Integration

- ✅ **TC-4.1.2**: Network error recovery
  - Input: Simulated network failure
  - Expected: Retry and reconnect
  - Test: Integration

- ✅ **TC-4.1.3**: Session stale detection
  - Input: Stale connection
  - Expected: Session recreated automatically
  - Test: Integration

- ✅ **TC-4.1.4**: Exponential backoff
  - Input: Multiple failures
  - Expected: Delays increase (1s, 2s, 4s)
  - Test: Unit

- ✅ **TC-4.1.5**: Max retry limit
  - Input: Persistent failure
  - Expected: Stops after 3 attempts
  - Test: Integration

- ✅ **TC-4.1.6**: Connection status indicator
  - Input: Connection state changes
  - Expected: UI updates correctly
  - Test: Frontend

#### Test Plan Updates:
- Document retry strategy
- List all failure scenarios
- Update when retry logic changes

---

### 4.2 Error Handling

#### Test Cases:
- ✅ **TC-4.2.1**: JIRA API 401 error
  - Input: Invalid token
  - Expected: Clear authentication error message
  - Test: Integration

- ✅ **TC-4.2.2**: JIRA API 403 error
  - Input: Insufficient permissions
  - Expected: Clear authorization error message
  - Test: Integration

- ✅ **TC-4.2.3**: JIRA API 404 error
  - Input: Invalid endpoint
  - Expected: Clear not found error
  - Test: Integration

- ✅ **TC-4.2.4**: JIRA API 500 error
  - Input: Server error
  - Expected: Retry with backoff
  - Test: Integration

- ✅ **TC-4.2.5**: Network timeout
  - Input: Slow/no response
  - Expected: Timeout error with retry
  - Test: Integration

- ✅ **TC-4.2.6**: Invalid JSON response (non-JSON content)
  - Input: HTML error page or non-JSON response from JIRA
  - Expected: Clear error message with response preview, no JSON parsing crash
  - Test: Integration
  - **Critical**: Must check content-type before parsing JSON

- ✅ **TC-4.2.7**: Error message display
  - Input: Various error types
  - Expected: User-friendly messages with tips
  - Test: Frontend

#### Test Plan Updates:
- Document all error scenarios
- List error message mappings
- Update when new errors discovered

---

## Current Implementation Status

### Recently Added Features (2024)

**New Fields Added:**
- ✅ **fixVersions** - Standard JIRA field for version tracking
- ✅ **customfield_23560** - Risk Indicator field
- ✅ **customfield_23073** - Status Update field with AI summarization

**AI Summarization Feature:**
- ✅ Created `backend/ai_summarizer.py` module
- ✅ Status Update field automatically summarized in executive-friendly format
- ✅ Frontend displays summary with expandable full text
- ✅ Summaries limited to 200 characters for readability

**Configuration:**
- ✅ All field IDs updated with actual JIRA field IDs
- ✅ Config file validated and working
- ✅ Display columns properly configured (10 columns total)

## Known Issues and Fixes

### Fixed Issues (2024)

**Bug Fix 1: Content-Type Header Logic (backend/app.py)**
- **Issue**: Contradictory logic in `after_request` function - conditional set followed by unconditional overwrite
- **Fix**: Removed redundant block, single conditional that only sets Content-Type if not already present
- **Status**: ✅ Fixed (commit cb028bb)
- **Impact**: Properly respects existing Content-Type headers

**Bug Fix 2: Pytest Coverage Configuration (pytest.ini)**
- **Issue**: Coverage paths pointed to root-level modules (`jira_client`, `app`) instead of `backend.jira_client`, `backend.app`
- **Fix**: Updated to `--cov=backend.jira_client` and `--cov=backend.app`
- **Status**: ✅ Fixed (commit 3873a1f)
- **Impact**: Coverage reports now correctly measure backend modules

## Previous Known Issues and Fixes

### Issue: JSON Parsing Errors
**Problem**: JIRA API sometimes returns non-JSON responses (HTML error pages, plain text, etc.) which caused "Expecting value: line 8 column 1 (char 7)" errors when parsed as JSON.

**Solution Implemented**:
- Check `Content-Type` header before parsing JSON
- Handle JSON parsing errors gracefully with try-catch
- Provide user-friendly error messages with response preview
- Test cases added: TC-1.1.6, TC-4.2.6

**Test Coverage**: All JSON parsing operations must verify content-type before parsing.

### Issue: Filter ID HTML Response
**Problem**: When using filter IDs (e.g., `filter=165194`), JIRA sometimes returns HTML pages instead of JSON, typically due to:
- Authentication failures (redirected to login page)
- Invalid JIRA URL configuration
- Insufficient permissions for the filter
- Filter doesn't exist or is not accessible

**Solution Implemented**:
- Detect HTML responses by checking `Content-Type` header **before** attempting JSON parse
- Provide specific error messages for HTML responses with actionable guidance
- Validate filter ID format (must be numeric) before API call
- Guide users to check authentication, URL, and permissions
- Test cases added: TC-1.1.7, TC-1.1.8, TC-1.1.9

**Test Coverage**: Filter ID handling must validate format and handle HTML responses gracefully.

**Error Message Example**:
```
JIRA returned an HTML page instead of JSON. This usually means:
- Authentication failed (check your JIRA_PAT_TOKEN)
- Invalid JIRA URL (check your JIRA_URL)
- Insufficient permissions for this filter/query
Please verify your credentials and JIRA URL in the .env file.
```

## Test Execution Checklist

### Before Each Commit:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Code coverage ≥ 90%
- [ ] Test plan updated if new features added
- [ ] No test warnings or errors

### Before Deployment:
- [ ] Full test suite passes
- [ ] End-to-end tests pass
- [ ] Performance tests pass
- [ ] Security tests pass
- [ ] Test documentation updated
- [ ] Test coverage report reviewed

### Test Maintenance:
- [ ] Update tests when features change
- [ ] Remove obsolete tests
- [ ] Refactor tests for maintainability
- [ ] Review test coverage regularly
- [ ] Update test plans quarterly

---

## Test Data and Fixtures

### Mock Data:
- Sample JIRA issues (various statuses)
- Sample changelog responses
- Sample field metadata
- Sample error responses
- **Non-JSON responses** (HTML error pages, plain text) for JSON parsing tests

### Test Fixtures:
- Valid configuration files
- Invalid configuration files
- Various JQL query formats
- Date history test data

### Code Quality Standards:
- **DRY Principle**: Extract shared utilities to avoid duplication
- **Lightweight**: Remove unused files and redundant code
- **Maintainability**: Use shared utility functions for common patterns
- **Best Practices**: Regular code cleanup and refactoring

### Environment Variable Handling in Tests:
**Important**: Unit tests use `@patch.dict('os.environ', ...)` to mock environment variables instead of loading from `.env` files.

**Why Mock Environment Variables?**
- **Test Isolation**: Tests should not depend on external files like `.env`
- **Reproducibility**: Tests work the same way for all developers
- **No Credentials Required**: Tests don't need actual JIRA credentials
- **Faster Execution**: No file I/O operations during tests

**How It Works:**
- `JiraClient` uses `load_dotenv()` which loads `.env` into `os.environ`
- Tests patch `os.environ` to simulate environment variables
- This is the standard Python testing pattern for environment variables
- Production code still uses `.env` files via `load_dotenv()`

**Test Pattern:**
```python
@patch.dict('os.environ', {
    'JIRA_URL': 'https://test.atlassian.net',
    'JIRA_PAT_TOKEN': 'test_token'
})
def test_something():
    client = JiraClient()  # Uses mocked env vars, not .env file
```

**Note**: This is NOT stale code - it's the correct pattern for unit test isolation.

---

## Phase 6: Story Points Calculation Tests

### 6.1 Work Item Filtering

#### Test Cases:
- ✅ **TC-6.1.1**: Task is identified as work item
  - Input: Issue type "Task"
  - Expected: Included in story points calculation
  - Test: Unit

- ✅ **TC-6.1.2**: Bug is identified as work item
  - Input: Issue type "Bug"
  - Expected: Included in story points calculation
  - Test: Unit

- ✅ **TC-6.1.3**: Test is identified as work item
  - Input: Issue type "Test"
  - Expected: Included in story points calculation
  - Test: Unit

- ✅ **TC-6.1.4**: Epic is excluded from work items
  - Input: Issue type "Epic"
  - Expected: Excluded from story points calculation
  - Test: Unit

- ✅ **TC-6.1.5**: Feature is excluded from work items
  - Input: Issue type "Feature"
  - Expected: Excluded from story points calculation
  - Test: Unit

- ✅ **TC-6.1.6**: Initiative is excluded from work items
  - Input: Issue type "Initiative"
  - Expected: Excluded from story points calculation
  - Test: Unit

- ✅ **TC-6.1.7**: X-FEAT is excluded from work items
  - Input: Issue type "X-FEAT"
  - Expected: Excluded from story points calculation
  - Test: Unit

- ✅ **TC-6.1.8**: Capability is excluded from work items
  - Input: Issue type "Capability"
  - Expected: Excluded from story points calculation
  - Test: Unit

### 6.2 Dev/QA Categorization

#### Test Cases:
- ✅ **TC-6.2.1**: Test issue type categorized as QA
  - Input: Issue type "Test"
  - Expected: Categorized as "QA"
  - Test: Unit

- ✅ **TC-6.2.2**: Test Plan issue type categorized as QA
  - Input: Issue type "Test Plan"
  - Expected: Categorized as "QA"
  - Test: Unit

- ✅ **TC-6.2.3**: Task issue type categorized as Dev
  - Input: Issue type "Task"
  - Expected: Categorized as "Dev"
  - Test: Unit

- ✅ **TC-6.2.4**: Bug issue type categorized as Dev
  - Input: Issue type "Bug"
  - Expected: Categorized as "Dev"
  - Test: Unit

### 6.3 Resolution Categorization

#### Test Cases:
- ✅ **TC-6.3.1**: Fixed resolution is positive
  - Input: Resolution "Fixed"
  - Expected: Categorized as "positive"
  - Test: Unit

- ✅ **TC-6.3.2**: Done resolution is positive
  - Input: Resolution "Done"
  - Expected: Categorized as "positive"
  - Test: Unit

- ✅ **TC-6.3.3**: Resolved resolution is positive
  - Input: Resolution "Resolved"
  - Expected: Categorized as "positive"
  - Test: Unit

- ✅ **TC-6.3.4**: Complete resolution is positive
  - Input: Resolution "Complete"
  - Expected: Categorized as "positive"
  - Test: Unit

- ✅ **TC-6.3.5**: Won't Do resolution is negative
  - Input: Resolution "Won't Do"
  - Expected: Categorized as "negative"
  - Test: Unit

- ✅ **TC-6.3.6**: Duplicate resolution is negative
  - Input: Resolution "Duplicate"
  - Expected: Categorized as "negative"
  - Test: Unit

- ✅ **TC-6.3.7**: No resolution is unresolved
  - Input: Resolution None
  - Expected: Categorized as "unresolved"
  - Test: Unit

### 6.4 Story Points Extraction

#### Test Cases:
- ✅ **TC-6.4.1**: Extract story points from customfield_10002
  - Input: Issue with customfield_10002 = 5.0
  - Expected: Returns 5.0
  - Test: Unit

- ✅ **TC-6.4.2**: Extract story points from configured field
  - Input: Issue with configured field ID
  - Expected: Returns correct value
  - Test: Unit

- ✅ **TC-6.4.3**: Missing story points returns 0.0
  - Input: Issue without story points field
  - Expected: Returns 0.0
  - Test: Unit

- ✅ **TC-6.4.4**: Integer story points converted to float
  - Input: Issue with story points = 3 (int)
  - Expected: Returns 3.0 (float)
  - Test: Unit

### 6.5 Story Points Breakdown Calculation

#### Test Cases:
- ✅ **TC-6.5.1**: Calculate breakdown for work items only
  - Input: Issues with Task (5 SP) and Epic (10 SP)
  - Expected: Only Task included (5 SP), Epic excluded
  - Test: Integration

- ✅ **TC-6.5.2**: Group story points by Dev/QA
  - Input: Task (5 SP) and Test (3 SP)
  - Expected: Dev = 5.0, QA = 3.0
  - Test: Integration

- ✅ **TC-6.5.3**: Categorize by resolution (positive/negative/unresolved)
  - Input: Done (5 SP), Won't Do (3 SP), Unresolved (2 SP)
  - Expected: Positive = 5.0, Negative = 3.0, Unresolved = 2.0
  - Test: Integration

- ✅ **TC-6.5.4**: Complex breakdown with multiple issues
  - Input: Multiple issues with different types and resolutions
  - Expected: Correct aggregation by Dev/QA and resolution
  - Test: Integration

- ✅ **TC-6.5.5**: Empty issue keys returns zero breakdown
  - Input: Empty list of issue keys
  - Expected: All values = 0.0
  - Test: Unit

### 6.6 Story Points Display Format

#### Test Cases:
- ✅ **TC-6.6.1**: Format breakdown shows only story points (no counts)
  - Input: Breakdown with story points
  - Expected: Display shows "Dev: X.X", "QA: X.X" (no counts)
  - Test: Unit

- ✅ **TC-6.6.2**: Format includes positive, negative, and unresolved
  - Input: Complete breakdown
  - Expected: All three categories displayed
  - Test: Unit

- ✅ **TC-6.6.3**: Format handles zero values
  - Input: Breakdown with zero story points
  - Expected: Displays "Dev: 0.0", "QA: 0.0"
  - Test: Unit

### 6.7 JQL Query Building

#### Test Cases:
- ✅ **TC-6.7.1**: Build JQL for single issue key
  - Input: ["ERA-48896"]
  - Expected: JQL includes key, Parent Link, portfolio children, etc.
  - Test: Unit

- ✅ **TC-6.7.2**: Build JQL for multiple issue keys
  - Input: ["ERA-48896", "ERA-44920"]
  - Expected: JQL includes all keys
  - Test: Unit

- ✅ **TC-6.7.3**: JQL includes all relationship types
  - Input: Issue keys
  - Expected: JQL includes key, Parent Link, FEAT ID, FEAT Number, portfolio children, epics, subtasks
  - Test: Unit

---

## Test Reporting

### Coverage Reports:
- Generate with: `pytest --cov=. --cov-report=html`
- Review coverage gaps
- Target: ≥90% coverage

### Test Results:
- All tests must pass
- Document any skipped tests
- Track test execution time
- Monitor flaky tests

---

## Continuous Improvement

- Review test effectiveness quarterly
- Update test plans based on bugs found
- Add tests for edge cases discovered
- Improve test performance
- Maintain test documentation

