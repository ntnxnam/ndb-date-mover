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

- ✅ **TC-2.1.6**: Changelog API error handling
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
  - Input: Query results
  - Expected: Table displays all columns correctly
  - Test: Frontend

- ✅ **TC-3.2.2**: Column sorting
  - Input: Click column header
  - Expected: Data sorted correctly
  - Test: Frontend

- ✅ **TC-3.2.3**: Column filtering
  - Input: Filter input
  - Expected: Table filtered correctly
  - Test: Frontend

- ✅ **TC-3.2.4**: Pagination
  - Input: Large dataset (1000+ issues)
  - Expected: Pagination works correctly
  - Test: Frontend + Integration

- ✅ **TC-3.2.5**: Empty table state
  - Input: No results
  - Expected: Appropriate empty state message
  - Test: Frontend

#### Test Plan Updates:
- Document table features
- List sorting/filtering options
- Update when table features added

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

- ✅ **TC-4.2.6**: Invalid JSON response
  - Input: HTML error page
  - Expected: Clear error message
  - Test: Integration

- ✅ **TC-4.2.7**: Error message display
  - Input: Various error types
  - Expected: User-friendly messages with tips
  - Test: Frontend

#### Test Plan Updates:
- Document all error scenarios
- List error message mappings
- Update when new errors discovered

---

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

### Test Fixtures:
- Valid configuration files
- Invalid configuration files
- Various JQL query formats
- Date history test data

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

