#!/bin/bash

# Fall Detection Lambda Testing Script
# This script runs tests for all lambda functions

echo "=========================================="
echo "FALL DETECTION LAMBDA TESTING SCRIPT"
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "test_all_lambdas.py" ]; then
    echo "Error: Please run this script from the src/lambdas directory"
    exit 1
fi

echo "Starting lambda tests..."
echo ""

# Run the comprehensive test suite
python3 test_all_lambdas.py

echo ""
echo "=========================================="
echo "TESTING COMPLETED"
echo "=========================================="

# Check if AWS CLI is available for additional testing
if command -v aws &> /dev/null; then
    echo ""
    echo "AWS CLI is available. You can also test with:"
    echo "  aws lambda invoke --function-name your-function-name --payload file://test-events/test.json response.json"
else
    echo ""
    echo "AWS CLI not found. Install it to test with real AWS services."
fi

echo ""
echo "For more detailed testing instructions, see TESTING_GUIDE.md"
