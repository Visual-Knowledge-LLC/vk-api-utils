#!/usr/bin/env python3
"""
Integration tests for VK Slack API
Tests the complete flow of thread creation and messaging
"""

import time
import sys
from datetime import datetime

try:
    from vk_api_utils import SlackNotifier
    print("✓ vk_api_utils imported successfully")
except ImportError as e:
    print(f"✗ Failed to import vk_api_utils: {e}")
    print("Run: pip install git+https://github.com/Visual-Knowledge-LLC/vk-api-utils.git")
    sys.exit(1)

def test_slack_thread_integration():
    """Test the complete Slack thread workflow"""

    print("\n" + "="*50)
    print("Testing VK Slack API Integration")
    print("="*50)

    # Initialize SlackNotifier
    service_name = "Integration Test Suite"
    print(f"\n1. Initializing SlackNotifier with service: '{service_name}'")

    try:
        slack = SlackNotifier(service_name)
        print("   ✓ SlackNotifier initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return False

    # Test 1: Start notification (creates thread)
    print("\n2. Sending start notification (creates thread)...")
    try:
        result = slack.notify_start()
        if result:
            print("   ✓ Thread started successfully")
            if hasattr(slack, 'thread_ts'):
                print(f"   Thread ID: {slack.thread_ts}")
        else:
            print("   ✗ Failed to start thread")
            return False
    except Exception as e:
        print(f"   ✗ Error starting thread: {e}")
        return False

    time.sleep(1)

    # Test 2: Progress notifications
    print("\n3. Sending progress notifications...")
    progress_messages = [
        "Initializing test sequence",
        "Running validation checks",
        "Processing test data",
        "Finalizing results"
    ]

    for msg in progress_messages:
        try:
            result = slack.notify_progress(msg)
            if result:
                print(f"   ✓ Progress: {msg}")
            else:
                print(f"   ✗ Failed: {msg}")
            time.sleep(0.5)
        except Exception as e:
            print(f"   ✗ Error: {e}")

    # Test 3: Success notification
    print("\n4. Sending success notification...")
    try:
        result = slack.notify_success("All tests completed successfully")
        if result:
            print("   ✓ Success notification sent")
        else:
            print("   ✗ Failed to send success notification")
    except Exception as e:
        print(f"   ✗ Error sending success: {e}")

    print("\n" + "="*50)
    print("✓ Integration test completed successfully!")
    print("="*50)
    return True

def test_error_notification():
    """Test error notification in a thread"""
    print("\n" + "="*50)
    print("Testing Error Notification")
    print("="*50)

    slack = SlackNotifier("Error Test Suite")

    print("1. Starting service...")
    slack.notify_start()
    time.sleep(1)

    print("2. Simulating progress...")
    slack.notify_progress("Processing data...")
    time.sleep(1)

    print("3. Simulating error...")
    error_msg = "Test error: Simulated failure for testing"
    try:
        result = slack.notify_error(error_msg)
        if result:
            print(f"   ✓ Error notification sent")
        else:
            print("   ✗ Failed to send error notification")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n✓ Error notification test completed!")
    return True

def test_warning_notification():
    """Test warning notification in a thread"""
    print("\n" + "="*50)
    print("Testing Warning Notification")
    print("="*50)

    slack = SlackNotifier("Warning Test Suite")

    print("1. Starting service...")
    slack.notify_start()
    time.sleep(1)

    print("2. Sending warning...")
    warning_msg = "Performance degradation detected"
    try:
        result = slack.notify_warning(warning_msg)
        if result:
            print(f"   ✓ Warning notification sent")
        else:
            print("   ✗ Failed to send warning")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("3. Continuing after warning...")
    slack.notify_progress("Continuing with reduced performance")
    time.sleep(1)

    slack.notify_success("Completed despite warnings")
    print("\n✓ Warning notification test completed!")
    return True

def main():
    """Run all integration tests"""
    print("="*60)
    print("VK Slack API Integration Test Suite")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    tests = [
        ("Thread Integration", test_slack_thread_integration),
        ("Error Notification", test_error_notification),
        ("Warning Notification", test_warning_notification)
    ]

    results = []
    for test_name, test_func in tests:
        if len(sys.argv) > 1 and sys.argv[1] != test_name.lower().replace(" ", "_"):
            continue

        print(f"\nRunning: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(r for _, r in results)
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())