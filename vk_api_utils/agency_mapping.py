"""
Agency mapping module for retrieving licensing agency information from the database.
This module provides a common interface for collectors to look up agency mappings
and header field mappings from the header_mappings table.

IMPORTANT: This module does NOT provide fallback mappings. If a mapping is not found
in the database, it will return None or raise an exception. This ensures data quality
and prevents incorrect data from being uploaded.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
from .database import get_db_session, get_engine

logger = logging.getLogger(__name__)


class MappingNotFoundError(Exception):
    """Raised when a required agency or header mapping is not found in the database"""
    pass


class AgencyMappingLookup:
    """
    Provides methods to look up agency information and header mappings
    from the database for use in data collectors.
    """

    def __init__(self, use_cache: bool = True, strict_mode: bool = True):
        """
        Initialize the agency mapping lookup.

        Args:
            use_cache: Whether to cache query results for performance
            strict_mode: If True, raise exceptions when mappings are not found.
                        If False, return None (but log warnings)
        """
        self.use_cache = use_cache
        self.strict_mode = strict_mode
        self._cache = {} if use_cache else None
        self._engine = None

    @property
    def engine(self):
        """Lazy load database engine"""
        if self._engine is None:
            self._engine = get_engine()
        return self._engine

    def get_header_mapping(self, dataset_key: str, state: Optional[str] = None) -> Optional[Dict]:
        """
        Get header mapping for a dataset from the database.

        Args:
            dataset_key: The dataset identifier (e.g., '0401', '1301B')
            state: Optional state code to filter by (e.g., 'TN', 'VA')

        Returns:
            Dictionary containing header mapping information

        Raises:
            MappingNotFoundError: If strict_mode is True and mapping is not found
        """
        # Check cache first
        cache_key = f"{dataset_key}_{state}" if state else dataset_key
        if self.use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # Format the key by adding a space and capitalizing if it contains alpha characters
        formatted_key = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', dataset_key).upper()

        query = """
        SELECT la.agency_id AS "Agency ID",
            hm.agency_name AS "Agency Name",
            hm.state AS "State Established",
            hm.business_name AS "Business Name",
            hm.street AS "Street",
            hm.zip AS "Zip",
            hm.date_established AS "Date Established",
            hm.category AS "Category",
            hm.license_number AS "License Number",
            hm.phone_number AS "Phone Number",
            hm.owner_first_name AS "Owner First Name",
            hm.owner_last_name AS "Owner Last Name",
            hm.expiration_date AS "Expiration Date",
            hm.license_status AS "License Status",
            hm.email AS "Email",
            hm.dataset AS "Dataset",
            hm.id AS "Mapping ID",
            hm.tobid AS "TOB ID",
            hm.agency_url AS "Agency URL",
            hm.county AS "County",
            hm.suspension_date AS "Suspension Date",
            hm.revocation_date AS "Revocation Date",
            hm.inactive_date AS "Inactive Date"
        FROM public.header_mappings AS hm
        JOIN licensing_agencies la ON hm.agency_name = la.agency_name
        WHERE hm.dataset LIKE %s
        """

        params = [f'{formatted_key}%']

        # Add state filter if provided
        if state:
            query += " AND hm.state = %s"
            params.append(state)

        query += " LIMIT 1"

        try:
            with get_db_session() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchone()

                    if result:
                        # Convert to dictionary using column names
                        columns = [desc[0] for desc in cursor.description]
                        header_mapping_dict = dict(zip(columns, result))

                        # Cache the result
                        if self.use_cache:
                            self._cache[cache_key] = header_mapping_dict

                        logger.debug(f"Found header mapping for {formatted_key}: {header_mapping_dict.get('Agency Name')}")
                        return header_mapping_dict
                    else:
                        error_msg = f"No header mappings found for dataset: {formatted_key}"
                        if state:
                            error_msg += f" in state: {state}"

                        if self.strict_mode:
                            logger.error(error_msg)
                            raise MappingNotFoundError(error_msg)
                        else:
                            logger.warning(error_msg)
                            return None

        except MappingNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Database query failed for {formatted_key}: {e}"
            logger.error(error_msg)
            if self.strict_mode:
                raise MappingNotFoundError(error_msg) from e
            return None

    def get_agency_by_name(self, agency_name: str) -> Optional[Dict]:
        """
        Get agency information by agency name.

        Args:
            agency_name: The name of the agency

        Returns:
            Dictionary containing agency information

        Raises:
            MappingNotFoundError: If strict_mode is True and agency is not found
        """
        if self.use_cache and f"agency_{agency_name}" in self._cache:
            return self._cache[f"agency_{agency_name}"]

        query = """
        SELECT agency_id, agency_name, state, bbb_id, agency_url, tob_id
        FROM licensing_agencies
        WHERE agency_name = %s
        LIMIT 1
        """

        try:
            with get_db_session() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, [agency_name])
                    result = cursor.fetchone()

                    if result:
                        columns = [desc[0] for desc in cursor.description]
                        agency_dict = dict(zip(columns, result))

                        if self.use_cache:
                            self._cache[f"agency_{agency_name}"] = agency_dict

                        return agency_dict
                    else:
                        error_msg = f"Agency not found: {agency_name}"
                        if self.strict_mode:
                            logger.error(error_msg)
                            raise MappingNotFoundError(error_msg)
                        else:
                            logger.warning(error_msg)
                            return None

        except MappingNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to get agency by name '{agency_name}': {e}"
            logger.error(error_msg)
            if self.strict_mode:
                raise MappingNotFoundError(error_msg) from e
            return None

    def get_agency_by_id(self, agency_id: int) -> Optional[Dict]:
        """
        Get agency information by agency ID.

        Args:
            agency_id: The numeric ID of the agency

        Returns:
            Dictionary containing agency information

        Raises:
            MappingNotFoundError: If strict_mode is True and agency is not found
        """
        if self.use_cache and f"agency_id_{agency_id}" in self._cache:
            return self._cache[f"agency_id_{agency_id}"]

        query = """
        SELECT agency_id, agency_name, state, bbb_id, agency_url, tob_id
        FROM licensing_agencies
        WHERE agency_id = %s
        LIMIT 1
        """

        try:
            with get_db_session() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, [agency_id])
                    result = cursor.fetchone()

                    if result:
                        columns = [desc[0] for desc in cursor.description]
                        agency_dict = dict(zip(columns, result))

                        if self.use_cache:
                            self._cache[f"agency_id_{agency_id}"] = agency_dict

                        return agency_dict
                    else:
                        error_msg = f"Agency not found with ID: {agency_id}"
                        if self.strict_mode:
                            logger.error(error_msg)
                            raise MappingNotFoundError(error_msg)
                        else:
                            logger.warning(error_msg)
                            return None

        except MappingNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to get agency by ID '{agency_id}': {e}"
            logger.error(error_msg)
            if self.strict_mode:
                raise MappingNotFoundError(error_msg) from e
            return None

    def get_agencies_by_state(self, state: str) -> List[Dict]:
        """
        Get all agencies for a specific state.

        Args:
            state: Two-letter state code (e.g., 'TN', 'VA')

        Returns:
            List of dictionaries containing agency information

        Raises:
            MappingNotFoundError: If strict_mode is True and no agencies found for state
        """
        query = """
        SELECT agency_id, agency_name, state, bbb_id, agency_url, tob_id
        FROM licensing_agencies
        WHERE state = %s
        ORDER BY agency_name
        """

        try:
            with get_db_session() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, [state.upper()])
                    results = cursor.fetchall()

                    if results:
                        columns = [desc[0] for desc in cursor.description]
                        return [dict(zip(columns, row)) for row in results]
                    else:
                        error_msg = f"No agencies found for state: {state}"
                        if self.strict_mode:
                            logger.error(error_msg)
                            raise MappingNotFoundError(error_msg)
                        else:
                            logger.warning(error_msg)
                            return []

        except MappingNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to get agencies for state '{state}': {e}"
            logger.error(error_msg)
            if self.strict_mode:
                raise MappingNotFoundError(error_msg) from e
            return []

    def verify_dataset_mappings(self, dataset_keys: List[str], state: Optional[str] = None) -> Dict[str, bool]:
        """
        Verify that mappings exist for a list of dataset keys.
        Useful for pre-flight checks before processing data.

        Args:
            dataset_keys: List of dataset identifiers to check
            state: Optional state code to filter by

        Returns:
            Dictionary mapping dataset_key to boolean (True if mapping exists)
        """
        results = {}
        missing = []

        for key in dataset_keys:
            try:
                mapping = self.get_header_mapping(key, state)
                results[key] = mapping is not None
                if not mapping:
                    missing.append(key)
            except MappingNotFoundError:
                results[key] = False
                missing.append(key)

        if missing:
            logger.warning(f"Missing mappings for datasets: {missing}")

        return results

    def clear_cache(self):
        """Clear the internal cache"""
        if self._cache:
            self._cache.clear()
            logger.debug("Agency mapping cache cleared")


# Create a global instance for convenience
_global_lookup = None


def get_agency_lookup(strict_mode: bool = True) -> AgencyMappingLookup:
    """
    Get a global instance of AgencyMappingLookup.
    This provides a singleton pattern for efficiency.

    Args:
        strict_mode: If True, raise exceptions when mappings not found

    Returns:
        AgencyMappingLookup instance
    """
    global _global_lookup
    if _global_lookup is None or _global_lookup.strict_mode != strict_mode:
        _global_lookup = AgencyMappingLookup(use_cache=True, strict_mode=strict_mode)
    return _global_lookup


# Convenience functions for direct access (all use strict_mode by default)
def get_header_mapping(dataset_key: str, state: Optional[str] = None) -> Dict:
    """
    Convenience function to get header mapping.
    Raises MappingNotFoundError if not found.
    """
    return get_agency_lookup(strict_mode=True).get_header_mapping(dataset_key, state)


def get_agency_by_name(agency_name: str) -> Dict:
    """
    Convenience function to get agency by name.
    Raises MappingNotFoundError if not found.
    """
    return get_agency_lookup(strict_mode=True).get_agency_by_name(agency_name)


def get_agency_by_id(agency_id: int) -> Dict:
    """
    Convenience function to get agency by ID.
    Raises MappingNotFoundError if not found.
    """
    return get_agency_lookup(strict_mode=True).get_agency_by_id(agency_id)


def get_agencies_by_state(state: str) -> List[Dict]:
    """
    Convenience function to get agencies by state.
    Raises MappingNotFoundError if no agencies found.
    """
    return get_agency_lookup(strict_mode=True).get_agencies_by_state(state)


if __name__ == "__main__":
    # Test the module when run directly
    import sys

    # Set up logging
    logging.basicConfig(level=logging.DEBUG)

    # Test connection first
    from .database import test_connection
    if not test_connection():
        print("❌ Cannot connect to database")
        sys.exit(1)

    # Create lookup instance
    lookup = AgencyMappingLookup(strict_mode=False)  # Use non-strict for testing

    # Test getting a header mapping
    print("\n📋 Testing header mapping lookup:")
    try:
        mapping = lookup.get_header_mapping("0401", "VA")
        if mapping:
            print(f"   Found mapping for VA dataset 0401:")
            print(f"   Agency: {mapping.get('Agency Name')}")
            print(f"   State: {mapping.get('State Established')}")
        else:
            print("   No mapping found for VA dataset 0401")
    except MappingNotFoundError as e:
        print(f"   Error: {e}")

    # Test getting Tennessee agencies
    print("\n🏢 Testing Tennessee agencies lookup:")
    try:
        tn_agencies = lookup.get_agencies_by_state("TN")
        if tn_agencies:
            print(f"   Found {len(tn_agencies)} Tennessee agencies")
            for agency in tn_agencies[:5]:  # Show first 5
                print(f"   - {agency['agency_name']} (ID: {agency['agency_id']})")
        else:
            print("   No Tennessee agencies found")
    except MappingNotFoundError as e:
        print(f"   Error: {e}")

    # Test strict mode
    print("\n⚠️  Testing strict mode (should raise exception):")
    strict_lookup = AgencyMappingLookup(strict_mode=True)
    try:
        # Try to get a non-existent mapping
        strict_lookup.get_header_mapping("NONEXISTENT", "XX")
    except MappingNotFoundError as e:
        print(f"   Correctly raised exception: {e}")

    print("\n✅ Agency mapping module test complete")