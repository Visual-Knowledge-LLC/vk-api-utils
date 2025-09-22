#!/usr/bin/env python3
"""
Test script for the agency mapping and database modules.
"""

import sys
import logging
from vk_api_utils import (
    test_connection,
    get_database_config,
    get_agencies_by_state,
    get_header_mapping,
    MappingNotFoundError
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test the agency mapping functionality"""

    # Test 1: Database Connection
    print("\n" + "="*50)
    print("🔌 Testing Database Connection")
    print("="*50)

    config = get_database_config()
    print(f"Database Config:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Database: {config['database']}")

    if not test_connection():
        print("❌ Database connection failed!")
        print("\nPlease ensure:")
        print("1. SSH tunnel is active (if running locally)")
        print("2. Database credentials are correct")
        sys.exit(1)

    print("✅ Database connection successful!")

    # Test 2: Get Tennessee Agencies
    print("\n" + "="*50)
    print("🏢 Testing Tennessee Agency Lookup")
    print("="*50)

    try:
        tn_agencies = get_agencies_by_state("TN")
        print(f"Found {len(tn_agencies)} Tennessee agencies:")

        # Show first 10
        for agency in tn_agencies[:10]:
            print(f"  • {agency['agency_name']} (ID: {agency['agency_id']}, BBB: {agency['bbb_id']})")

    except MappingNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nThis likely means there are no Tennessee agencies in the database.")
        print("Please verify the licensing_agencies table has Tennessee data.")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 3: Test Header Mapping
    print("\n" + "="*50)
    print("📋 Testing Header Mapping Lookup")
    print("="*50)

    # Test with a known dataset (you may need to adjust this based on your data)
    test_datasets = [
        ("0401", "VA"),  # Virginia DPOR example
        ("103", "TN"),   # Tennessee example (adjust as needed)
    ]

    for dataset_key, state in test_datasets:
        print(f"\n  Testing dataset '{dataset_key}' for state '{state}':")
        try:
            mapping = get_header_mapping(dataset_key, state)
            if mapping:
                print(f"    ✅ Found mapping:")
                print(f"       Agency: {mapping.get('Agency Name')}")
                print(f"       Agency ID: {mapping.get('Agency ID')}")
                print(f"       State: {mapping.get('State Established')}")
        except MappingNotFoundError as e:
            print(f"    ⚠️  No mapping found: {e}")
            print(f"       This dataset needs to be added to header_mappings table")
        except Exception as e:
            print(f"    ❌ Error: {e}")

    # Test 4: Test strict mode behavior
    print("\n" + "="*50)
    print("⚠️  Testing Strict Mode (Expected to Fail)")
    print("="*50)

    try:
        # This should raise an exception
        fake_mapping = get_header_mapping("NONEXISTENT_KEY", "XX")
        print("❌ Unexpected: Should have raised MappingNotFoundError")
    except MappingNotFoundError as e:
        print(f"✅ Correctly raised exception for missing mapping:")
        print(f"   {e}")

    print("\n" + "="*50)
    print("✨ All tests completed!")
    print("="*50)


if __name__ == "__main__":
    main()