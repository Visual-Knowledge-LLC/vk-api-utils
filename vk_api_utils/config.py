"""
Configuration management for VK API Utils
"""
import os
from typing import Optional

class Config:
    """Central configuration for VK API connections"""

    # API URLs
    BASE_API_URL = os.environ.get("VK_API_URL", "https://api.visualknowledgeportal.com")
    SLACK_API_URL = os.environ.get("VK_SLACK_API_URL", f"{BASE_API_URL}/slack/slack")  # Note: nginx proxies /slack/* to the service
    SLACK_API_PORT = 8347  # Unique port for Slack API service

    # Authentication
    SLACK_API_KEY = os.environ.get("VK_SLACK_API_KEY", "vk-etl-prod-2025")

    # Slack settings
    DEFAULT_SLACK_CHANNEL = os.environ.get("VK_SLACK_CHANNEL", "default")

    # Timeout settings
    DEFAULT_TIMEOUT = 30

    @classmethod
    def get_slack_url(cls, endpoint: str = "") -> str:
        """Get full Slack API URL with optional endpoint"""
        base = cls.SLACK_API_URL
        if endpoint:
            return f"{base}/{endpoint.lstrip('/')}"
        return base

    @classmethod
    def get_api_headers(cls, api_key: Optional[str] = None) -> dict:
        """Get standard API headers"""
        return {
            "X-API-Key": api_key or cls.SLACK_API_KEY,
            "Content-Type": "application/json"
        }