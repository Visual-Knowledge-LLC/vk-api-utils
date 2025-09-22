"""
VK API Utils - Unified API client library for Visual Knowledge services

This package provides:
- Slack integration for alerts and notifications
- Configuration management
- Database connection with environment detection
- Agency mapping lookups from header_mappings table
"""

__version__ = "0.2.0"

from .slack import SlackClient, SlackNotifier
from .config import Config
from .database import (
    get_database_config,
    get_connection,
    get_engine,
    get_db_session,
    test_connection,
    detect_environment
)
from .agency_mapping import (
    AgencyMappingLookup,
    get_agency_lookup,
    get_header_mapping,
    get_agency_by_name,
    get_agency_by_id,
    get_agencies_by_state,
    MappingNotFoundError
)

__all__ = [
    # Slack
    "SlackClient",
    "SlackNotifier",
    # Config
    "Config",
    # Database
    "get_database_config",
    "get_connection",
    "get_engine",
    "get_db_session",
    "test_connection",
    "detect_environment",
    # Agency Mapping
    "AgencyMappingLookup",
    "get_agency_lookup",
    "get_header_mapping",
    "get_agency_by_name",
    "get_agency_by_id",
    "get_agencies_by_state",
    "MappingNotFoundError"
]