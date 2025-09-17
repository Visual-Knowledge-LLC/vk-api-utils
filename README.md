# VK API Utils

Centralized API utilities and client libraries for Visual Knowledge services.

## Overview

This repository provides unified API clients and utilities for interacting with VK's various API endpoints and services.

## Installation

```bash
pip install -e .
```

Or include in requirements.txt:
```
git+https://github.com/Visual-Knowledge-LLC/vk-api-utils.git
```

## Available Modules

### Slack API Client
- Send messages to Slack channels
- Create and manage threaded conversations
- Full async support

### Usage

```python
from vk_api_utils.slack import SlackClient

# Initialize client
slack = SlackClient(
    api_url="https://api.visualknowledgeportal.com/slack",
    api_key="your-api-key"
)

# Send a message
slack.send_message("Hello from VK!", channel="general")

# Create a thread
thread = slack.start_thread(
    title="Daily Report",
    initial_message="Starting processing...",
    channel="automation"
)

# Reply to thread
slack.reply_to_thread(
    thread_ts=thread["thread_ts"],
    message="Processing complete!"
)
```

## Configuration

### Environment Variables
- `VK_API_URL`: Base URL for VK APIs (default: https://api.visualknowledgeportal.com)
- `VK_SLACK_API_KEY`: API key for Slack API
- `VK_SLACK_CHANNEL`: Default Slack channel

## API Endpoints

### Production
- Main API: https://api.visualknowledgeportal.com
- Slack API: https://api.visualknowledgeportal.com/slack (port 8347)

## Development

```bash
# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/

# Format code
black vk_api_utils/
```

## License

Proprietary - Visual Knowledge LLC