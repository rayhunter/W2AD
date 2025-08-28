# Manual Testing Scenarios

This directory contains manual test scenarios for user acceptance testing of the WordPress-to-Astro migration tool.

## Overview

These tests are designed to be executed manually by developers or QA testers to verify end-to-end functionality and user experience. Each test scenario includes:

- **Prerequisites**: What needs to be set up before testing
- **Steps**: Detailed step-by-step instructions
- **Expected Results**: What should happen at each step
- **Verification**: How to confirm the test passed

## Test Scenarios

### 1. [Basic Migration Test](test_basic_migration.md)
Test the complete migration pipeline with a simple WordPress site.

### 2. [Authentication Test](test_authentication.md)
Test various authentication scenarios for WordPress and GitHub integration.

### 3. [Content Validation Test](test_content_validation.md)
Test content transformation and sanitization with problematic content.

### 4. [Media Migration Test](test_media_migration.md)
Test media file migration to Google Cloud Storage.

### 5. [CMS Integration Test](test_cms_integration.md)
Test the generated Decap CMS admin interface.

### 6. [GitHub Integration Test](test_github_integration.md)
Test repository creation and code deployment to GitHub.

### 7. [Cloudflare Deployment Test](test_cloudflare_deployment.md)
Test complete migration pipeline with Cloudflare Pages deployment.

### 8. [Error Handling Test](test_error_handling.md)
Test error scenarios and recovery mechanisms.

### 9. [Performance Test](test_performance.md)
Test migration performance with large amounts of content.

## Running Manual Tests

1. **Environment Setup**:
   ```bash
   cd WP2ASTRO+Decap
   source virtual/bin/activate  # or venv/bin/activate
   streamlit run app.py
   ```

2. **Test Data**: 
   - Use the test WordPress sites documented in each scenario
   - Or set up your own test WordPress instance

3. **Credentials Required**:
   - GitHub Personal Access Token
   - Google Cloud Storage credentials (for media tests)
   - WordPress credentials (for private content tests)

4. **Documentation**:
   - Record any bugs or unexpected behavior
   - Take screenshots of key steps
   - Note performance metrics where applicable

## Test Environment

- **Local Development**: `http://localhost:8501`
- **Test WordPress Sites**: Various public WordPress sites for testing
- **Test GitHub Account**: Use a dedicated test account for GitHub operations

## Reporting Issues

When reporting issues found during manual testing:

1. **Scenario**: Which test scenario was being executed
2. **Step**: Exact step where the issue occurred
3. **Expected**: What should have happened
4. **Actual**: What actually happened
5. **Environment**: Browser, OS, Python version, etc.
6. **Reproducible**: Steps to reproduce the issue
7. **Screenshots**: Visual evidence of the issue

## Test Status Tracking

| Test Scenario | Status | Last Tested | Notes |
|---------------|--------|-------------|-------|
| Basic Migration | ✅ Pass | 2024-01-15 | All functionality working |
| Authentication | ⏳ Pending | - | Needs testing |
| Content Validation | ⏳ Pending | - | Needs testing |
| Media Migration | ⏳ Pending | - | Needs testing |
| CMS Integration | ⏳ Pending | - | Needs testing |
| GitHub Integration | ⏳ Pending | - | Needs testing |
| Cloudflare Deployment | ⏳ Pending | - | New DeployAgent test |
| Error Handling | ⏳ Pending | - | Needs testing |
| Performance | ⏳ Pending | - | Needs testing |

Legend:
- ✅ Pass: Test completed successfully
- ❌ Fail: Test failed, issues need to be resolved
- ⏳ Pending: Test not yet executed
- 🔄 In Progress: Test currently being executed

## Notes

- Manual tests complement the automated pytest suite
- Focus on user experience and edge cases not covered by unit tests
- Update test scenarios as new features are added
- Regular execution recommended before major releases
