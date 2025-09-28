#!/usr/bin/env python3
"""
Simple test runner for all lambda functions.
Run this script to test all lambdas locally.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and display results."""
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    """Main test runner function."""
    print("FALL DETECTION LAMBDA TEST RUNNER")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("test_all_lambdas.py").exists():
        print("Error: Please run this script from the src/lambdas directory")
        sys.exit(1)
    
    # Test individual lambda examples
    print("\n1. Testing Transcribe Lambda Example...")
    success1 = run_command(
        "cd transcribe-invoke-lambda && python3 test_example.py",
        "Transcribe Lambda Test Example"
    )
    
    print("\n2. Testing Video Lambda Example...")
    success2 = run_command(
        "cd video-invoke-lambda && python3 test_example.py",
        "Video Lambda Test Example"
    )
    
    print("\n3. Testing Action Lambda Example...")
    success3 = run_command(
        "cd action-lambda && python3 test_example.py",
        "Action Lambda Test Example"
    )
    
    print("\n4. Running Comprehensive Test Suite...")
    success4 = run_command(
        "python3 test_all_lambdas.py",
        "Comprehensive Test Suite"
    )
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    tests = [
        ("Transcribe Lambda", success1),
        ("Video Lambda", success2),
        ("Action Lambda", success3),
        ("Comprehensive Suite", success4)
    ]
    
    passed = 0
    for test_name, success in tests:
        status = "PASSED" if success else "FAILED"
        print(f"{test_name:20} : {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Your lambdas are ready for deployment.")
    else:
        print(f"\n⚠️  {len(tests) - passed} test(s) failed. Check the output above for details.")
    
    print("\nNext steps:")
    print("1. Deploy your lambdas to AWS")
    print("2. Configure environment variables")
    print("3. Test with real AWS services using the test events in test-events/")
    print("4. Monitor CloudWatch logs for any issues")

if __name__ == "__main__":
    main()
