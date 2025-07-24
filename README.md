# S3 Log Replicator

A serverless, event-driven solution for cross-account S3 log file replication using AWS CloudFormation, Lambda, and SQS.

## Overview

This solution provides a fully automated log ingestion pipeline that copies vendor logs into your environment as soon as they're available, with proper monitoring and error handling built in.

### Architecture Flow

1. **Vendor drops log files** into their S3 bucket
2. **S3 bucket sends notifications** to their SQS queue
3. **Lambda function monitors** their SQS queue (cross-account)
4. **Lambda downloads** the file from their S3 bucket
5. **Lambda uploads** the file to your destination S3 bucket
6. **SQS message gets deleted**, process repeats

### Why This Approach

- **Event-driven** - No polling, only runs when files actually show up
- **Serverless** - No infrastructure to manage, scales automatically
- **Cost-effective** - Only pay for what you use
- **Clean separation** - Vendor handles their side, you handle yours
- **Flexible** - Can point to any destination bucket via parameters

## Prerequisites

- AWS CLI installed and configured
- Appropriate AWS permissions to create CloudFormation stacks
- Vendor's SQS queue ARN and S3 bucket name
- Destination S3 bucket (will be created if it doesn't exist)

## Components

### CloudFormation Template (`template.yaml`)

The main infrastructure template that creates:

- **Lambda Function** - Processes SQS messages and copies S3 objects
- **IAM Role** - Cross-account permissions for Lambda
- **CloudWatch Logs** - Centralized logging with configurable retention
- **CloudWatch Alarms** - Error and performance monitoring
- **SNS Topic** - Alarm notifications
- **CloudWatch Dashboard** - Real-time metrics visualization
- **SQS Event Source Mapping** - Triggers Lambda on SQS messages

### Lambda Function (`lambda_function.py`)

The core logic that:
- Processes SQS messages containing S3 notifications
- Downloads files from vendor S3 bucket
- Uploads files to destination S3 bucket
- Handles errors gracefully with detailed logging
- Supports both S3 notification formats

### Manual Deployment

The solution can be deployed manually using AWS CLI commands with proper parameter validation and monitoring.

## Deployment

### Prerequisites

- AWS CLI installed and configured
- Appropriate AWS permissions to create CloudFormation stacks
- Vendor's SQS queue ARN and S3 bucket name
- Destination S3 bucket (will be created if it doesn't exist)

### Quick Start

1. **Create a parameters file** (`parameters.json`):
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
     },
     {
       "ParameterKey": "LambdaTimeout",
       "ParameterValue": "300"
     },
     {
       "ParameterKey": "LambdaMemorySize",
       "ParameterValue": "512"
     },
     {
       "ParameterKey": "LogRetentionDays",
       "ParameterValue": "30"
     }
   ]
   ```

2. **Deploy the CloudFormation stack**:
   ```bash
   aws cloudformation create-stack \
     --stack-name s3-log-replicator \
     --template-body file://template.yaml \
     --parameters file://parameters.json \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-east-1 \
     --tags Key=Environment,Value=dev Key=Project,Value=S3LogReplicator
   ```

3. **Wait for deployment to complete**:
   ```bash
   aws cloudformation wait stack-create-complete \
     --stack-name s3-log-replicator \
     --region us-east-1
   ```

### Example Deployments

**Development Environment**:
```bash
# Create parameters file
cat > parameters-dev.json << EOF
[
  {
    "ParameterKey": "VendorSQSQueueARN",
    "ParameterValue": "arn:aws:sqs:us-east-1:123456789012:dev-vendor-queue"
  },
  {
    "ParameterKey": "VendorS3BucketName",
    "ParameterValue": "dev-vendor-logs"
  },
  {
    "ParameterKey": "DestinationS3BucketName",
    "ParameterValue": "dev-destination-logs"
  },
  {
    "ParameterKey": "LambdaTimeout",
    "ParameterValue": "180"
  },
  {
    "ParameterKey": "LambdaMemorySize",
    "ParameterValue": "256"
  },
  {
    "ParameterKey": "LogRetentionDays",
    "ParameterValue": "7"
  }
]
EOF

# Deploy stack
aws cloudformation create-stack \
  --stack-name dev-s3-log-replicator \
  --template-body file://template.yaml \
  --parameters file://parameters-dev.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --tags Key=Environment,Value=dev Key=Project,Value=S3LogReplicator
```

**Production Environment**:
```bash
# Create parameters file
cat > parameters-prod.json << EOF
[
  {
    "ParameterKey": "VendorSQSQueueARN",
    "ParameterValue": "arn:aws:sqs:us-east-1:123456789012:prod-vendor-queue"
  },
  {
    "ParameterKey": "VendorS3BucketName",
    "ParameterValue": "prod-vendor-logs"
  },
  {
    "ParameterKey": "DestinationS3BucketName",
    "ParameterValue": "prod-destination-logs"
  },
  {
    "ParameterKey": "LambdaTimeout",
    "ParameterValue": "300"
  },
  {
    "ParameterKey": "LambdaMemorySize",
    "ParameterValue": "1024"
  },
  {
    "ParameterKey": "LogRetentionDays",
    "ParameterValue": "90"
  }
]
EOF

# Deploy stack
aws cloudformation create-stack \
  --stack-name prod-s3-log-replicator \
  --template-body file://template.yaml \
  --parameters file://parameters-prod.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --tags Key=Environment,Value=prod Key=Project,Value=S3LogReplicator
```

### Updating the Stack

To update the stack with new parameters:

```bash
aws cloudformation update-stack \
  --stack-name s3-log-replicator \
  --template-body file://template.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Deleting the Stack

To remove the stack and all resources:

```bash
aws cloudformation delete-stack \
  --stack-name s3-log-replicator \
  --region us-east-1

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete \
  --stack-name s3-log-replicator \
  --region us-east-1
```

## What We Need from the Vendor

### Required Information

1. **SQS Queue ARN** - The ARN of their SQS queue that receives S3 notifications
2. **S3 Bucket Name** - The name of their S3 bucket containing log files

### Required IAM Permissions

The vendor needs to grant your Lambda execution role the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_STACK_NAME-lambda-execution-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::VENDOR_BUCKET_NAME/*"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_STACK_NAME-lambda-execution-role"
      },
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:REGION:VENDOR_ACCOUNT_ID:VENDOR_QUEUE_NAME"
    }
  ]
}
```

## Monitoring and Alerts

### CloudWatch Dashboard

The deployment creates a CloudWatch dashboard with:
- Lambda function metrics (invocations, errors, throttles)
- Lambda function duration
- SQS queue metrics (messages received, sent, deleted)

### CloudWatch Alarms

Two alarms are created:
1. **Lambda Errors** - Triggers when Lambda function encounters errors
2. **Lambda Duration** - Triggers when Lambda execution time approaches timeout

### SNS Notifications

Alarms send notifications to an SNS topic. Subscribe to this topic to receive:
- Email notifications
- Slack/Teams webhooks
- SMS messages
- Custom HTTP endpoints

## Testing

### Test the System

1. **Upload a test file** to the vendor S3 bucket
2. **Check CloudWatch logs** for Lambda execution
3. **Verify file appears** in destination S3 bucket
4. **Monitor CloudWatch dashboard** for metrics

### Test Commands

```bash
# Check Lambda function logs
aws logs tail /aws/lambda/STACK_NAME-log-replicator --follow

# Test S3 copy manually
aws s3 cp s3://vendor-bucket/test-file.log s3://destination-bucket/test-file.log

# Check SQS queue status
aws sqs get-queue-attributes --queue-url https://sqs.region.amazonaws.com/account/queue-name --attribute-names All
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Verify cross-account IAM permissions
   - Check Lambda execution role permissions
   - Ensure vendor has granted necessary access

2. **Lambda Timeout**
   - Increase Lambda timeout parameter
   - Check for large files that may take longer to copy
   - Monitor CloudWatch logs for performance issues

3. **SQS Message Processing Errors**
   - Verify SQS queue ARN format
   - Check SQS queue permissions
   - Review Lambda function logs for message format issues

4. **S3 Copy Failures**
   - Verify source bucket and object exist
   - Check destination bucket permissions
   - Ensure sufficient Lambda memory for large files

### Debug Commands

```bash
# Get stack status
aws cloudformation describe-stacks --stack-name STACK_NAME

# Get Lambda function configuration
aws lambda get-function --function-name STACK_NAME-log-replicator

# Check IAM role permissions
aws iam get-role --role-name STACK_NAME-lambda-execution-role

# View recent CloudWatch logs
aws logs describe-log-streams --log-group-name /aws/lambda/STACK_NAME-log-replicator --order-by LastEventTime --descending --max-items 5
```

## Security Considerations

### IAM Best Practices

- **Principle of Least Privilege** - Lambda role has minimal required permissions
- **Cross-Account Access** - Specific ARN-based permissions for vendor resources
- **No Hardcoded Credentials** - Uses IAM roles and temporary credentials

### Data Protection

- **Encryption in Transit** - All S3 and SQS communications are encrypted
- **Encryption at Rest** - S3 objects are encrypted by default
- **Audit Logging** - All actions are logged in CloudWatch

### Network Security

- **VPC Isolation** - Lambda runs in AWS-managed VPC
- **No Public Access** - All resources are private by default

## Cost Optimization

### Lambda Optimization

- **Memory Configuration** - Adjust based on file sizes and processing needs
- **Timeout Settings** - Set appropriate timeouts to avoid unnecessary charges
- **Batch Processing** - Process multiple SQS messages per invocation

### S3 Cost Considerations

- **Storage Classes** - Consider using S3-IA or Glacier for older logs
- **Lifecycle Policies** - Automate moving files to cheaper storage
- **Cross-Region Replication** - Additional costs for cross-region copying

### Monitoring Costs

- **CloudWatch Logs** - Configure appropriate retention periods
- **CloudWatch Metrics** - Standard metrics are free, custom metrics have costs
- **SNS Notifications** - Minimal cost for alarm notifications

## Support and Maintenance

### Regular Maintenance

1. **Monitor CloudWatch Alarms** - Respond to alerts promptly
2. **Review Logs** - Check for errors or performance issues
3. **Update Dependencies** - Keep Lambda runtime updated
4. **Review Permissions** - Audit IAM roles periodically

### Scaling Considerations

- **Lambda Concurrency** - Monitor for throttling
- **SQS Queue Depth** - Watch for message backlog
- **S3 Transfer Rates** - Consider for high-volume scenarios

## License

This project is provided as-is for educational and commercial use. Please ensure compliance with AWS terms of service and your organization's security policies.

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review CloudWatch logs
3. Consult AWS documentation
4. Contact your AWS support team if needed 