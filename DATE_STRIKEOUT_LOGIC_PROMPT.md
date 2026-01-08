# Date Strike-Out Logic Implementation Prompt

## Overview
This prompt describes the logic for displaying historical dates with strike-through formatting for specific JIRA custom date fields. The implementation tracks date changes over time and displays them with the current date prominently and historical dates struck out.

## Target Fields
The following JIRA custom fields should track date history:
- `customfield_13861` (FS/DS done date)
- `customfield_11068` (Test plan date)
- `customfield_11067` (Code Complete Date)
- `customfield_35863` (Commit Gate)
- `customfield_35864` (Promotion Gate)

## Core Requirements

### 1. Date History Extraction from JIRA Changelog

**Source**: JIRA API changelog (using `expand=changelog` parameter or `/rest/api/2/issue/{issueKey}?expand=changelog`)

**Process**:
1. Fetch changelog for each issue
2. Filter changelog entries where `field` matches the target custom field ID (e.g., `customfield_13861`)
3. Extract the `to` value (the new date value after change) and `timestamp` from each change entry
4. Store as list of tuples: `[(date_value, timestamp), ...]`
5. Sort by timestamp chronologically (oldest first)

**Changelog Entry Structure**:
```json
{
  "field": "customfield_13861",
  "field_original": "11067",  // May be numeric or customfield_ format
  "field_name": "Code Complete Date",
  "from": "2025-01-10",
  "to": "2025-01-15",
  "timestamp": "2025-01-12T10:30:00.000+0000"
}
```

**Important Notes**:
- Field IDs in changelog may be numeric (e.g., `11067`) or in `customfield_` format (e.g., `customfield_11067`)
- Normalize field IDs: convert numeric IDs to `customfield_` format for matching
- If `fieldId` is missing, resolve from field metadata using field name

### 2. Date Formatting

**Display Format**: Always use `dd/mmm/yyyy` format (e.g., `15/Jan/2026`)

**Month Abbreviations**:
```
Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
```

**Input Format Support**:
The system must parse dates in multiple formats:
- ISO 8601: `2025-01-15T10:30:00.000+0000` or `2025-01-15`
- Already formatted: `15/Jan/2025` or `15/Jan/25`
- Numeric: `15/01/2025` (DD/MM/YYYY) or `01/15/2025` (MM/DD/YYYY)

**Formatting Function Logic**:
1. Try parsing with standard datetime formats (ISO, numeric)
2. If that fails, use regex to parse `dd/mmm/yyyy` or `dd/mmm/yy` format
3. Handle 2-digit years: if year < 50, assume 2000s; if >= 50, assume 1900s
4. Convert to `dd/mmm/yyyy` format (e.g., `15/Jan/2026`)

### 3. Current Date Exclusion (CRITICAL)

**Requirement**: The current date value must NEVER appear in the struck-out history list.

**Comparison Methods** (use all three for robustness):

**Method 1: Normalized Comparison**
- Normalize both dates to `YYYY-MM-DD` format
- Compare normalized strings
- If equal, exclude from history

**Method 2: String Comparison**
- Compare raw date strings directly
- If equal, exclude from history

**Method 3: Formatted Comparison**
- Format both dates to `dd/mmm/yyyy`
- Compare formatted strings
- Also normalize formatted dates and compare (handles `13/Jun/2025` vs `13/Jun/25`)
- If equal, exclude from history

**Normalization Function**:
```python
def normalize_date_for_comparison(date_str: str) -> Optional[str]:
    """
    Normalize date to YYYY-MM-DD format for comparison.
    Parses date in various formats and returns ISO date string.
    """
    # Parse date using multiple format attempts
    # Return as "YYYY-MM-DD" or None if parsing fails
```

### 4. History Processing and Deduplication

**Process**:
1. Iterate through date history (oldest to newest)
2. For each historical date:
   - Normalize for comparison
   - Check if it matches current date (using all 3 comparison methods)
   - If matches current date, SKIP it
   - Check if normalized date already seen (deduplication)
   - If duplicate, SKIP it
   - Format date to `dd/mmm/yyyy`
   - Add to history list
3. Reverse the list to show newest first, oldest last

**Deduplication**:
- Track seen dates using normalized format (`YYYY-MM-DD`)
- If normalization fails, use original string as fallback
- Only add unique dates to history

### 5. Display Format

**Structure**:
```
Current Date (bold, prominent)
├─ Historical Date 1 (struck out, gray, smaller font)
├─ Historical Date 2 (struck out, gray, smaller font)
└─ Historical Date 3 (struck out, gray, smaller font)
```

**CSS Styling**:
```css
.date-current {
    font-weight: 600;
    color: #333;
}

.date-history {
    font-size: 0.85em;
    color: #999;
    margin-top: 4px;
}

.date-history span {
    text-decoration: line-through;
    display: block;
    margin-bottom: 2px;
}
```

**HTML Structure**:
```html
<div class="date-cell">
    <div class="date-current">15/Jan/2026</div>
    <div class="date-history">
        <span>10/Jan/2026</span>
        <span>05/Jan/2026</span>
    </div>
</div>
```

### 6. Order of Historical Dates

**Display Order**: Reverse chronological (newest historical date first, oldest last)

**Processing Order**:
1. Extract dates from changelog (sorted by timestamp, oldest first)
2. Filter out current date and duplicates
3. Format all historical dates
4. Reverse the list before display

### 7. Edge Cases

**Same Date in Different Formats**:
- `13/Jun/2025` vs `13/Jun/25` should be treated as the same date
- Use normalization to `YYYY-MM-DD` for comparison

**Missing Dates**:
- If current value is empty/null, don't show date cell
- If no history exists, only show current date (no history section)

**Invalid Dates**:
- If date parsing fails, log warning and return original string
- Don't break the entire display if one date fails

**Reverts**:
- If date changes A → B → A, both A and B should appear in history (if A is not current)
- Count all changes, including reverts

## Implementation Steps

### Step 1: Fetch Changelog
```python
# Pseudo-code
changelog = fetch_issue_changelog(issue_key)
# Returns list of change entries
```

### Step 2: Extract Date History
```python
date_history = []
for change in changelog:
    if change.field == target_field_id:
        date_history.append((change.to, change.timestamp))

# Sort by timestamp (oldest first)
date_history.sort(key=lambda x: x[1])
```

### Step 3: Process and Format
```python
current_date = issue.fields[target_field_id]
formatted_history = []
seen_dates = set()

for date_val, timestamp in date_history:
    # Normalize for comparison
    date_normalized = normalize_date_for_comparison(date_val)
    current_normalized = normalize_date_for_comparison(current_date)
    
    # Skip if matches current date
    if date_normalized == current_normalized:
        continue
    
    # Skip duplicates
    if date_normalized in seen_dates:
        continue
    seen_dates.add(date_normalized)
    
    # Format and add
    formatted_history.append(format_date(date_val, "dd/mmm/yyyy"))

# Reverse to show newest first
formatted_history.reverse()
```

### Step 4: Display
```html
<div class="date-cell">
    <div class="date-current">{{ formatted_current_date }}</div>
    {{#if formatted_history.length}}
    <div class="date-history">
        {{#each formatted_history}}
        <span>{{ this }}</span>
        {{/each}}
    </div>
    {{/if}}
</div>
```

## Example Output

**Input**:
- Current date: `2026-01-15`
- History: `2026-01-10`, `2026-01-05`, `2025-12-20`

**Output**:
```
15/Jan/2026  (current, bold)
~~10/Jan/2026~~  (struck out, gray)
~~05/Jan/2026~~  (struck out, gray)
~~20/Dec/2025~~  (struck out, gray)
```

## Testing Checklist

- [ ] Current date is never in struck-out history
- [ ] Dates are formatted as `dd/mmm/yyyy`
- [ ] Historical dates are in reverse chronological order (newest first)
- [ ] Duplicate dates are removed
- [ ] Same date in different formats (e.g., `13/Jun/2025` vs `13/Jun/25`) are treated as same
- [ ] Empty/null current date doesn't break display
- [ ] Invalid dates are handled gracefully
- [ ] All 5 target fields work correctly

## Notes for Different Technologies

**For React/JavaScript**:
- Use `moment.js` or `date-fns` for date parsing and formatting
- Use CSS classes for strike-through styling
- Store history in component state or props

**For Python/Django**:
- Use `datetime` module for parsing
- Use template filters for formatting
- Pass history as context to templates

**For Other Frameworks**:
- Adapt the core logic (extraction, normalization, comparison, formatting)
- Use framework-specific date libraries
- Apply CSS/styling according to framework conventions

## Key Functions to Implement

1. **`normalize_date_for_comparison(date_str)`**: Returns `YYYY-MM-DD` format
2. **`format_date(date_str, format)`**: Returns `dd/mmm/yyyy` format
3. **`extract_date_history(changelog, field_id)`**: Returns list of (date, timestamp) tuples
4. **`process_date_history(date_history, current_date)`**: Filters, deduplicates, formats, and reverses

