# Quick Start Testing Guide

This guide will get you testing your lambda functions in under 5 minutes!

## 🚀 Quick Start (Local Testing)

### 1. Run All Tests at Once
```bash
cd src/lambdas
python3 run_tests.py
```

This will run all lambda test examples and give you a summary.

### 2. Test Individual Lambdas

**Transcribe Lambda:**
```bash
cd src/lambdas/transcribe-invoke-lambda
python3 test_example.py
```

**Video Lambda:**
```bash
cd src/lambdas/video-invoke-lambda
python3 test_example.py
```

**Action Lambda:**
```bash
cd src/lambdas/action-lambda
python3 test_example.py
```

## 🧪 Test Scenarios

### Transcribe Lambda Tests
- ✅ Normal activity audio
- ✅ Fall detection audio
- ✅ Emergency situation audio
- ✅ Multi-speaker conversations
- ✅ Bedrock analysis integration

### Video Lambda Tests
- ✅ Normal activity video
- ✅ Fall detection video
- ✅ Emergency situation video
- ✅ Person tracking analysis
- ✅ Safety scoring

### Action Lambda Tests
- ✅ Fall detected actions
- ✅ Emergency alert actions
- ✅ Normal activity actions
- ✅ SNS notification simulation
- ✅ Polly synthesis simulation

## 🔧 AWS Testing (After Deployment)

### 1. Test with AWS CLI
```bash
# Test transcribe lambda
aws lambda invoke \
  --function-name transcribe-invoke-lambda \
  --payload file://test-events/transcribe-test.json \
  response.json

# Test video lambda
aws lambda invoke \
  --function-name video-invoke-lambda \
  --payload file://test-events/video-test.json \
  response.json

# Test action lambda
aws lambda invoke \
  --function-name action-lambda \
  --payload file://test-events/action-fall-detected.json \
  response.json
```

### 2. Test with AWS Console
1. Go to AWS Lambda Console
2. Select your function
3. Click "Test"
4. Create test event using JSON from `test-events/` folder
5. Execute and view results

## 📊 Expected Results

### Successful Test Output
```
FALL DETECTION LAMBDA TEST RUNNER
============================================================

RUNNING: Transcribe Lambda Test Example
============================================================
Testing Audio Transcription Scenario...
Transcription Results:
Text: Hello, I'm just walking around the room.
Length: 45 characters
Speakers: 1 detected

Testing Fall Detection Audio Scenario...
Fall Detection Transcription:
Text: Oh no! I think I fell down.
Fall Keywords Found: ['fall', 'fell']
Risk Level: HIGH

... (more test output)

TEST SUMMARY
============================================================
Transcribe Lambda    : PASSED
Video Lambda         : PASSED
Action Lambda        : PASSED
Comprehensive Suite  : PASSED

Total: 4/4 tests passed

🎉 All tests passed! Your lambdas are ready for deployment.
```

## 🐛 Troubleshooting

### Common Issues

**Import Errors:**
- Make sure you're running from the `src/lambdas` directory
- Check that all Python files are in the correct locations

**Missing Dependencies:**
```bash
pip install boto3 botocore
```

**Permission Errors:**
```bash
chmod +x run_tests.py
python3 run_tests.py
```

### Getting Help

1. Check the detailed `TESTING_GUIDE.md` for comprehensive instructions
2. Look at individual test files in each lambda directory
3. Check CloudWatch logs if testing on AWS
4. Verify environment variables are set correctly

## 📁 Test Files Structure

```
src/lambdas/
├── test_all_lambdas.py          # Comprehensive test suite
├── run_tests.py                 # Simple test runner
├── TESTING_GUIDE.md             # Detailed testing guide
├── QUICK_START_TESTING.md       # This file
├── test-events/                 # Sample test events
│   ├── transcribe-test.json
│   ├── transcribe-fall-detected.json
│   ├── video-test.json
│   ├── video-fall-detected.json
│   ├── action-fall-detected.json
│   └── action-normal.json
├── transcribe-invoke-lambda/
│   └── test_example.py
├── video-invoke-lambda/
│   └── test_example.py
└── action-lambda/
    └── test_example.py
```

## 🎯 Next Steps

1. **Run local tests** to verify functionality
2. **Deploy to AWS** using your CDK stack
3. **Configure environment variables** in AWS
4. **Test with real AWS services** using the test events
5. **Monitor CloudWatch logs** for any issues
6. **Set up SNS topics** for notifications
7. **Configure S3 buckets** for storage

Happy testing! 🚀
