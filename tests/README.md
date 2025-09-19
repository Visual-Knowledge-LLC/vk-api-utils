# VK API Utils Tests

## Integration Tests

### test_slack_integration.py
Full integration test for the Slack API functionality.

**Usage:**
```bash
# Run all tests
python tests/test_slack_integration.py

# Run specific test
python tests/test_slack_integration.py thread_integration
python tests/test_slack_integration.py error_notification
python tests/test_slack_integration.py warning_notification
```

**What it tests:**
- Thread creation with `notify_start()`
- Progress updates staying in thread with `notify_progress()`
- Success notifications with `notify_success()`
- Error notifications with `notify_error()`
- Warning notifications with `notify_warning()`

**Requirements:**
- vk-api-utils installed
- VK_SLACK_API_KEY environment variable (or uses default)
- Access to VK Slack API server

## Unit Tests
*To be added*

## Running Tests
```bash
# From the repository root
cd ~/vk-api-utils
python -m pytest tests/  # When pytest tests are added
python tests/test_slack_integration.py  # Run integration tests
```