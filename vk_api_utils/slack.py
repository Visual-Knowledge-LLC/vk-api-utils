"""
Slack API client for VK services
"""
import os
import json
import logging
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from .config import Config

logger = logging.getLogger(__name__)


class SlackClient:
    """Low-level Slack API client"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize Slack API client

        Args:
            api_url: Slack API URL (defaults to Config.SLACK_API_URL)
            api_key: API key for authentication (defaults to Config.SLACK_API_KEY)
            timeout: Request timeout in seconds
        """
        self.api_url = api_url or Config.SLACK_API_URL
        self.api_key = api_key or Config.SLACK_API_KEY
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(Config.get_api_headers(self.api_key))

    def send_message(self, text: str, channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a simple message to Slack

        Args:
            text: Message text
            channel: Target channel (defaults to Config.DEFAULT_SLACK_CHANNEL)

        Returns:
            API response data
        """
        endpoint = f"{self.api_url}/message"
        payload = {
            "text": text,
            "channel": channel or Config.DEFAULT_SLACK_CHANNEL
        }

        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise

    def start_thread(
        self,
        title: str,
        initial_message: str,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new Slack thread

        Args:
            title: Thread title
            initial_message: Initial message content
            channel: Target channel

        Returns:
            API response with thread_ts
        """
        endpoint = f"{self.api_url}/thread/start"
        payload = {
            "title": title,
            "initial_message": initial_message,
            "channel": channel or Config.DEFAULT_SLACK_CHANNEL
        }

        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start Slack thread: {e}")
            raise

    def reply_to_thread(
        self,
        thread_ts: str,
        message: str,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reply to an existing thread

        Args:
            thread_ts: Thread timestamp
            message: Reply message
            channel: Target channel

        Returns:
            API response data
        """
        endpoint = f"{self.api_url}/thread/reply"
        payload = {
            "thread_ts": thread_ts,
            "message": message,
            "channel": channel or Config.DEFAULT_SLACK_CHANNEL
        }

        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to reply to Slack thread: {e}")
            raise

    def health_check(self) -> bool:
        """Check if Slack API is healthy"""
        endpoint = f"{self.api_url}/health"
        try:
            response = self.session.get(endpoint, timeout=5)
            return response.status_code == 200
        except:
            return False


class SlackNotifier:
    """High-level Slack notification handler for services"""

    def __init__(
        self,
        service_name: str,
        enabled: bool = True,
        client: Optional[SlackClient] = None,
        channel: Optional[str] = None
    ):
        """
        Initialize Slack notifier

        Args:
            service_name: Name of the service for identification
            enabled: Whether notifications are enabled
            client: SlackClient instance (creates new if None)
            channel: Default channel for notifications
        """
        self.service_name = service_name
        self.enabled = enabled
        self.channel = channel or Config.DEFAULT_SLACK_CHANNEL
        self.client = client or SlackClient()
        self.thread_ts = None
        self.start_time = None

    def notify_start(self, details: Optional[Dict[str, Any]] = None) -> bool:
        """Notify service start and create thread"""
        if not self.enabled:
            return True

        self.start_time = datetime.now()
        timestamp = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        title = f"🚀 {self.service_name} Started"

        initial_message = f"Service: {self.service_name}\nStarted: {timestamp}"
        if details:
            initial_message += f"\n{self._format_details(details)}"

        try:
            result = self.client.start_thread(title, initial_message, self.channel)
            self.thread_ts = result.get("thread_ts")
            return True
        except Exception as e:
            logger.warning(f"Failed to send start notification: {e}")
            return False

    def notify_progress(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send progress update to thread"""
        if not self.enabled or not self.thread_ts:
            return True

        formatted_message = message
        if details:
            formatted_message += f"\n{self._format_details(details)}"

        try:
            self.client.reply_to_thread(self.thread_ts, formatted_message, self.channel)
            return True
        except Exception as e:
            logger.warning(f"Failed to send progress notification: {e}")
            return False

    def notify_success(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Notify successful completion"""
        if not self.enabled:
            return True

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Calculate duration if we have start time
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            duration_str = self._format_duration(duration)
            final_message = f"✅ SUCCESS [{timestamp}] (Duration: {duration_str})\n{message}"
        else:
            final_message = f"✅ SUCCESS [{timestamp}]\n{message}"

        if details:
            final_message += f"\n{self._format_details(details)}"

        if self.thread_ts:
            try:
                self.client.reply_to_thread(self.thread_ts, final_message, self.channel)
                return True
            except Exception as e:
                logger.warning(f"Failed to send success notification: {e}")
                return False
        else:
            # No thread, send as regular message
            try:
                self.client.send_message(final_message, self.channel)
                return True
            except Exception as e:
                logger.warning(f"Failed to send success notification: {e}")
                return False

    def notify_error(
        self,
        error: str,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ) -> bool:
        """Notify error condition"""
        if not self.enabled:
            return True

        timestamp = datetime.now().strftime("%H:%M:%S")
        error_message = f"❌ ERROR [{timestamp}]\n{error}"

        if exception:
            error_message += f"\nException: {str(exception)}"

        if details:
            error_message += f"\n{self._format_details(details)}"

        if self.thread_ts:
            try:
                self.client.reply_to_thread(self.thread_ts, error_message, self.channel)
                return True
            except Exception as e:
                logger.warning(f"Failed to send error notification: {e}")
                return False
        else:
            # No thread, send as regular message
            try:
                self.client.send_message(error_message, self.channel)
                return True
            except Exception as e:
                logger.warning(f"Failed to send error notification: {e}")
                return False

    def notify_warning(
        self,
        warning: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Notify warning condition"""
        if not self.enabled:
            return True

        timestamp = datetime.now().strftime("%H:%M:%S")
        warning_message = f"⚠️ WARNING [{timestamp}]\n{warning}"

        if details:
            warning_message += f"\n{self._format_details(details)}"

        if self.thread_ts:
            try:
                self.client.reply_to_thread(self.thread_ts, warning_message, self.channel)
                return True
            except Exception as e:
                logger.warning(f"Failed to send warning notification: {e}")
                return False
        else:
            # No thread, send as regular message
            try:
                self.client.send_message(warning_message, self.channel)
                return True
            except Exception as e:
                logger.warning(f"Failed to send warning notification: {e}")
                return False

    def notify_metric(
        self,
        metric_name: str,
        value: Any,
        unit: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Notify metric/measurement"""
        if not self.enabled:
            return True

        message = f"📊 {metric_name}: {value}"
        if unit:
            message += f" {unit}"

        return self.notify_progress(message, details)

    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format details dictionary for Slack message"""
        lines = []
        for key, value in details.items():
            formatted_key = key.replace("_", " ").title()

            if isinstance(value, (list, tuple)):
                if len(value) > 5:
                    value = f"{', '.join(str(v) for v in value[:5])}, ... ({len(value)} total)"
                else:
                    value = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                value = json.dumps(value, indent=2)
            elif isinstance(value, float):
                value = f"{value:.2f}"

            lines.append(f"• {formatted_key}: {value}")

        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    @classmethod
    def from_args(cls, service_name: str, args) -> "SlackNotifier":
        """
        Create SlackNotifier from argparse args

        Args:
            service_name: Name of the service
            args: Argparse namespace with optional 'slack' attribute

        Returns:
            SlackNotifier instance
        """
        slack_enabled = True
        if hasattr(args, 'slack'):
            slack_enabled = args.slack.lower() != 'off'

        return cls(service_name, enabled=slack_enabled)