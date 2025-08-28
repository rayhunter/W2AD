# Error Handling Test

**Objective**: Verify that the application gracefully handles various error scenarios and provides helpful feedback to users.

**Duration**: ~30-40 minutes

**Prerequisites**:
- Tool is running locally (`streamlit run app.py`)
- Access to various test scenarios (invalid URLs, credentials, etc.)

## Test Steps

### Scenario 1: Invalid WordPress URLs

#### Test 1A: Malformed URL
1. Navigate to "1. ExtractionAgent"
2. Enter invalid URL: `not-a-valid-url`
3. Attempt to start migration

**Expected Result**: Clear error message about invalid URL format, migration does not proceed.

#### Test 1B: Non-existent Domain
1. Enter URL: `https://this-domain-does-not-exist-12345.com`
2. Attempt connection

**Expected Result**: Network error with helpful message about unreachable domain.

#### Test 1C: Valid Domain, No WordPress
1. Enter URL: `https://google.com`
2. Attempt connection

**Expected Result**: Error indicating site is not a WordPress site or REST API not available.

#### Test 1D: WordPress Site with Disabled REST API
1. Find a WordPress site with disabled REST API (or simulate)
2. Attempt extraction

**Expected Result**: Error message explaining REST API is not accessible.

### Scenario 2: GitHub Authentication Errors

#### Test 2A: Invalid Token Format
1. Navigate to "6. GitHubAgent"
2. Enter invalid token: `invalid_token_format`
3. Attempt to start migration

**Expected Result**: Clear error about invalid GitHub token format.

#### Test 2B: Expired Token
1. Use an expired GitHub token (or revoked token)
2. Attempt repository creation

**Expected Result**: Authentication error with instructions to generate new token.

#### Test 2C: Insufficient Permissions
1. Use token without `repo` scope
2. Attempt to create repository

**Expected Result**: Permission error explaining required token scopes.

#### Test 2D: Repository Already Exists
1. Use existing repository name
2. Attempt creation

**Expected Result**: Error about repository already existing, suggestion to use different name.

### Scenario 3: Google Cloud Storage Errors

#### Test 3A: Invalid Credentials Path
1. Navigate to "3. MediaAgent"
2. Enable media migration
3. Enter non-existent credentials path: `/fake/path/credentials.json`
4. Attempt migration

**Expected Result**: File not found error with clear guidance about credentials.

#### Test 3B: Invalid Credentials File
1. Create fake JSON file with invalid credentials
2. Use this file for GCS setup
3. Attempt migration

**Expected Result**: Authentication error with GCS, helpful error message.

#### Test 3C: Non-existent Bucket
1. Use valid credentials but non-existent bucket name: `fake-bucket-name-12345`
2. Attempt media migration

**Expected Result**: Bucket not found error with helpful guidance.

#### Test 3D: Insufficient Bucket Permissions
1. Use service account with read-only permissions
2. Attempt media upload

**Expected Result**: Permission denied error with guidance about required permissions.

### Scenario 4: Content Processing Errors

#### Test 4A: WordPress Site with No Content
1. Use WordPress site with zero posts/pages
2. Attempt migration

**Expected Result**: Warning about no content found, but migration should complete.

#### Test 4B: Extremely Large Content
1. Use WordPress site with very large posts (>1MB content per post)
2. Attempt migration

**Expected Result**: Should handle gracefully, may show progress indicators.

#### Test 4C: Malformed HTML Content
1. Use site with severely malformed HTML
2. Verify content transformation

**Expected Result**: html2text should handle gracefully, content may be cleaned up.

#### Test 4D: Unicode and Special Characters
1. Use site with emoji, special characters, non-Latin scripts
2. Verify content processing

**Expected Result**: Unicode preserved correctly, no encoding errors.

### Scenario 5: Network and Connectivity Issues

#### Test 5A: Network Timeout
1. Simulate slow network (use browser dev tools or network throttling)
2. Attempt migration with large WordPress site

**Expected Result**: Appropriate timeout errors, retry mechanisms if implemented.

#### Test 5B: Intermittent Connectivity
1. Temporarily disconnect internet during migration
2. Observe behavior

**Expected Result**: Network errors with clear explanation, migration fails gracefully.

#### Test 5C: GitHub API Rate Limiting
1. Trigger rate limiting (difficult to simulate, document expected behavior)

**Expected Result**: Rate limit error with information about retry timing.

### Scenario 6: File System Errors

#### Test 6A: Insufficient Disk Space
1. Fill up disk space (or simulate)
2. Attempt migration

**Expected Result**: Disk space error with clear message.

#### Test 6B: Permission Denied
1. Set output directory to read-only
2. Attempt project creation

**Expected Result**: Permission error with guidance about directory access.

#### Test 6C: Invalid Project Path
1. Use invalid characters in project path
2. Attempt migration

**Expected Result**: Path validation error with helpful message.

### Scenario 7: Application State Errors

#### Test 7A: Rapid Successive Migrations
1. Start migration
2. Immediately start another migration
3. Observe behavior

**Expected Result**: Either queue properly or prevent concurrent operations with clear message.

#### Test 7B: Browser Refresh During Migration
1. Start migration
2. Refresh browser page
3. Check application state

**Expected Result**: Session state handled gracefully, clear indication of current status.

#### Test 7C: Long-Running Migration
1. Use large WordPress site
2. Let migration run for extended time
3. Check for timeouts or memory issues

**Expected Result**: No memory leaks, appropriate progress indicators, completion or timeout.

## Error Message Quality Tests

For each error scenario above, verify error messages:

### Message Content Checklist
- [ ] **Clear**: Error message is understandable to non-technical users
- [ ] **Specific**: Indicates exactly what went wrong
- [ ] **Actionable**: Provides steps to resolve the issue
- [ ] **Context**: Shows which part of the process failed
- [ ] **Recovery**: Indicates if retry is possible

### Example Good Error Messages
```
❌ GitHub Authentication Failed
Invalid GitHub token. Please check that your token:
• Has not expired
• Includes 'repo' or 'public_repo' scope
• Is entered correctly without extra spaces

Generate a new token at: https://github.com/settings/tokens
```

```
❌ WordPress Site Not Found
Could not connect to https://invalid-site.com
• Check that the URL is correct
• Ensure the site is accessible from your network
• Verify the site is a WordPress site with REST API enabled

Try a different URL or check your network connection.
```

## Recovery and Resilience Tests

### Test 8A: Recovery After Error
1. Trigger any error from above scenarios
2. Fix the issue (correct URL, token, etc.)
3. Attempt migration again

**Expected Result**: Application recovers cleanly, no residual state issues.

### Test 8B: Partial Failure Recovery
1. Start migration that will fail partway through (e.g., GitHub fails after content extraction)
2. Fix the issue
3. Determine if partial progress is preserved

**Expected Result**: Clear indication of what completed, ability to continue or restart cleanly.

### Test 8C: Error During File Operations
1. Simulate file operation failure during project creation
2. Verify cleanup and error handling

**Expected Result**: No partial files left behind, clear error message, clean recovery.

## Verification Checklist

For each error scenario:
- [ ] Error detected and reported clearly
- [ ] User gets actionable information
- [ ] Application doesn't crash or become unresponsive
- [ ] No data corruption or partial states
- [ ] Recovery possible after fixing issue
- [ ] Error logged appropriately for debugging
- [ ] User interface remains functional

## Performance Under Error Conditions

- [ ] Application remains responsive during error handling
- [ ] Memory usage doesn't spike during errors
- [ ] UI doesn't freeze or become unclickable
- [ ] Error display doesn't break page layout

## Logging and Debugging

- [ ] Errors logged with sufficient detail for debugging
- [ ] Sensitive information (tokens, passwords) not logged in plaintext
- [ ] Log levels appropriate (ERROR for failures, WARNING for issues)
- [ ] Timestamps and context included in logs

## Success Criteria

✅ **Test Passes If**:
- All error scenarios are handled gracefully
- Error messages are clear and actionable
- Application remains stable after errors
- Users can recover from errors by following guidance
- No crashes or unhandled exceptions

❌ **Test Fails If**:
- Application crashes on any error scenario
- Error messages are unclear or unhelpful
- Users cannot recover from errors
- Partial state corruption occurs
- UI becomes unresponsive during error handling

## Common Error Categories

**User Input Errors**: Invalid URLs, credentials, configuration
- Should be caught early with validation
- Clear guidance for correction

**External Service Errors**: GitHub API, WordPress API, GCS issues
- Should include service-specific error codes
- Suggestions for resolution

**System Errors**: File system, network, memory issues
- Should be logged for debugging
- User-friendly explanations

**Application Errors**: Logic errors, unexpected states
- Should be logged with full context
- Graceful degradation where possible
