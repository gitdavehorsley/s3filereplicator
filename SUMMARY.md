# S3 Log Replicator - Project Summary

This project provides a complete serverless solution for cross-account S3 log file replication using AWS CloudFormation, Lambda, and SQS.

## Project Files

### Core Infrastructure
- **`template.yaml`** - Main CloudFormation template with all AWS resources
- **`lambda_function.py`** - Lambda function code for processing SQS messages and copying S3 objects

### Documentation
- **`README.md`** - Comprehensive guide covering deployment, monitoring, and troubleshooting
- **`vendor-setup-guide.md`** - Complete guide for vendors to set up their side of the system

## Architecture Overview

```
Vendor S3 Bucket → SQS Queue → Lambda Function → Destination S3 Bucket
```

### Key Components

1. **Lambda Function** - Processes SQS messages and copies S3 objects
2. **IAM Role** - Cross-account permissions for Lambda
3. **CloudWatch Logs** - Centralized logging with configurable retention
4. **CloudWatch Alarms** - Error and performance monitoring
5. **SNS Topic** - Alarm notifications
6. **CloudWatch Dashboard** - Real-time metrics visualization
7. **SQS Event Source Mapping** - Triggers Lambda on SQS messages

## Quick Start

1. **Get vendor information**:
   - SQS Queue ARN
   - S3 Bucket Name

2. **Create parameters file** (`parameters.json`):
   ```json
   [
     {
       "ParameterKey": "VendorSQSQueueARN",
       "ParameterValue": "arn:aws:sqs:us-east-1:123456789012:vendor-queue"
     },
     {
       "ParameterKey": "VendorS3BucketName",
       "ParameterValue": "vendor-logs-bucket"
     },
     {
       "ParameterKey": "DestinationS3BucketName",
       "ParameterValue": "my-destination-bucket"
     }
   ]
   ```

3. **Deploy the stack**:
   ```bash
   aws cloudformation create-stack \
     --stack-name s3-log-replicator \
     --template-body file://template.yaml \
     --parameters file://parameters.json \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-east-1
   ```

## Features

- ✅ **Event-driven** - No polling, only runs when files appear
- ✅ **Serverless** - No infrastructure to manage, scales automatically
- ✅ **Cost-effective** - Only pay for what you use
- ✅ **Cross-account** - Works with vendor AWS accounts
- ✅ **Monitoring** - CloudWatch logs, alarms, and dashboard
- ✅ **Error handling** - Graceful error handling with detailed logging
- ✅ **Security** - IAM roles with least privilege access

## What You Need from the Vendor

1. **SQS Queue ARN** - Their SQS queue that receives S3 notifications
2. **S3 Bucket Name** - Their S3 bucket containing log files
3. **Cross-account permissions** - They need to grant your Lambda role access

## Next Steps

1. Review the `README.md` for detailed deployment instructions
2. Check `vendor-setup-guide.md` for vendor configuration requirements
3. Deploy the CloudFormation stack using AWS CLI
4. Test the system by uploading files to the vendor S3 bucket
5. Monitor the CloudWatch dashboard for metrics

## Support

For questions or issues:
1. Check the troubleshooting section in `README.md`
2. Review CloudWatch logs for error details
3. Verify cross-account permissions are correctly configured
4. Test with AWS CLI commands as shown in the documentation 