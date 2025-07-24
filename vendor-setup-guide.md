# Vendor Setup Guide for S3 Log Replication

This guide helps vendors set up their side of the S3 log replication system to enable cross-account log file copying.

## Overview

As a vendor, you need to configure your AWS account to:
1. Set up S3 bucket notifications to SQS
2. Grant cross-account permissions to the customer's Lambda function
3. Provide the necessary ARNs and bucket names to the customer

## Prerequisites

- AWS account with appropriate permissions
- S3 bucket containing log files
- SQS queue to receive S3 notifications
- Customer's Lambda execution role ARN

## Step 1: Create SQS Queue

Create an SQS queue to receive S3 bucket notifications:

```bash
# Create SQS queue
aws sqs create-queue \
    --queue-name "vendor-logs-queue" \
    --attributes '{
        "MessageRetentionPeriod": "1209600",
        "VisibilityTimeout": "30",
        "ReceiveMessageWaitTimeSeconds": "20"
    }'

# Get queue ARN (you'll need this for the customer)
aws sqs get-queue-attributes \
    --queue-url "https://sqs.REGION.amazonaws.com/ACCOUNT-ID/vendor-logs-queue" \
    --attribute-names QueueArn
```

## Step 2: Configure S3 Bucket Notifications

Configure your S3 bucket to send notifications to the SQS queue:

```bash
# Create S3 bucket notification configuration
aws s3api put-bucket-notification-configuration \
    --bucket "your-logs-bucket" \
    --notification-configuration '{
        "QueueConfigurations": [
            {
                "Id": "LogFileNotifications",
                "QueueArn": "arn:aws:sqs:REGION:ACCOUNT-ID:vendor-logs-queue",
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {
                                "Name": "suffix",
                                "Value": ".log"
                            }
                        ]
                    }
                }
            }
        ]
    }'
```

## Step 3: Grant Cross-Account Permissions

### S3 Bucket Policy

Add a bucket policy to allow the customer's Lambda function to read objects:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCustomerLambdaReadAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::CUSTOMER_ACCOUNT_ID:role/CUSTOMER_STACK_NAME-lambda-execution-role"
            },
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion"
            ],
            "Resource": "arn:aws:s3:::your-logs-bucket/*"
        }
    ]
}
```

Apply the policy:

```bash
aws s3api put-bucket-policy \
    --bucket "your-logs-bucket" \
    --policy file://bucket-policy.json
```

### SQS Queue Policy

Add a queue policy to allow the customer's Lambda function to receive and delete messages:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCustomerLambdaSQSAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::CUSTOMER_ACCOUNT_ID:role/CUSTOMER_STACK_NAME-lambda-execution-role"
            },
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes"
            ],
            "Resource": "arn:aws:sqs:REGION:ACCOUNT-ID:vendor-logs-queue"
        }
    ]
}
```

Apply the policy:

```bash
aws sqs set-queue-attributes \
    --queue-url "https://sqs.REGION.amazonaws.com/ACCOUNT-ID/vendor-logs-queue" \
    --attributes '{
        "Policy": "'$(cat queue-policy.json | jq -c .)'"
    }'
```

## Step 4: CloudFormation Template (Optional)

You can also use this CloudFormation template to set up the vendor side:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Vendor S3 Log Replication Setup'

Parameters:
  CustomerAccountId:
    Type: String
    Description: 'Customer AWS Account ID'
    AllowedPattern: '^[0-9]{12}$'
  
  CustomerLambdaRoleName:
    Type: String
    Description: 'Customer Lambda execution role name'
    Default: 's3-log-replicator-lambda-execution-role'
  
  LogBucketName:
    Type: String
    Description: 'Name of the S3 bucket containing log files'
    AllowedPattern: '^[a-z0-9][a-z0-9.-]*[a-z0-9]$'

Resources:
  # SQS Queue
  VendorLogsQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub '${AWS::StackName}-vendor-logs-queue'
      MessageRetentionPeriod: 1209600  # 14 days
      VisibilityTimeout: 30
      ReceiveMessageWaitTimeSeconds: 20
      QueuePolicy:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${CustomerAccountId}:role/${CustomerLambdaRoleName}'
            Action:
              - sqs:ReceiveMessage
              - sqs:DeleteMessage
              - sqs:GetQueueAttributes
            Resource: !GetAtt VendorLogsQueue.Arn

  # S3 Bucket
  LogBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref LogBucketName
      NotificationConfiguration:
        QueueConfigurations:
          - Event: s3:ObjectCreated:*
            Queue: !GetAtt VendorLogsQueue.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: suffix
                    Value: .log

  # S3 Bucket Policy
  LogBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref LogBucket
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${CustomerAccountId}:role/${CustomerLambdaRoleName}'
            Action:
              - s3:GetObject
              - s3:GetObjectVersion
            Resource: !Sub '${LogBucket}/*'

Outputs:
  VendorSQSQueueARN:
    Description: 'ARN of the vendor SQS queue'
    Value: !GetAtt VendorLogsQueue.Arn
    Export:
      Name: !Sub '${AWS::StackName}-vendor-sqs-queue-arn'

  VendorS3BucketName:
    Description: 'Name of the vendor S3 bucket'
    Value: !Ref LogBucket
    Export:
      Name: !Sub '${AWS::StackName}-vendor-s3-bucket-name'
```

## Step 5: Provide Information to Customer

Provide the following information to your customer:

1. **SQS Queue ARN**: `arn:aws:sqs:REGION:ACCOUNT-ID:vendor-logs-queue`
2. **S3 Bucket Name**: `your-logs-bucket`
3. **AWS Region**: The region where your resources are located

## Step 6: Testing

### Test S3 to SQS Notification

1. Upload a test log file to your S3 bucket:
   ```bash
   echo "test log content" > test.log
   aws s3 cp test.log s3://your-logs-bucket/
   ```

2. Check if the message appears in your SQS queue:
   ```bash
   aws sqs receive-message \
       --queue-url "https://sqs.REGION.amazonaws.com/ACCOUNT-ID/vendor-logs-queue" \
       --max-number-of-messages 10
   ```

### Test Cross-Account Access

Ask your customer to test the cross-account access by:
1. Deploying their CloudFormation stack
2. Uploading a test file to your S3 bucket
3. Verifying the file appears in their destination bucket

## Monitoring and Troubleshooting

### CloudWatch Metrics

Monitor your SQS queue and S3 bucket:

```bash
# Check SQS queue metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/SQS \
    --metric-name NumberOfMessagesReceived \
    --dimensions Name=QueueName,Value=vendor-logs-queue \
    --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Sum

# Check S3 bucket metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/S3 \
    --metric-name NumberOfObjects \
    --dimensions Name=BucketName,Value=your-logs-bucket \
    --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average
```

### Common Issues

1. **Permission Denied Errors**
   - Verify the customer's Lambda role ARN is correct
   - Check that bucket and queue policies are properly applied
   - Ensure the customer account ID is correct

2. **SQS Messages Not Received**
   - Verify S3 bucket notification configuration
   - Check SQS queue policy allows S3 to send messages
   - Ensure file extensions match the filter rules

3. **Cross-Account Access Issues**
   - Verify both S3 and SQS policies are in place
   - Check that the customer's Lambda role exists
   - Ensure the customer has deployed their stack

## Security Best Practices

1. **Principle of Least Privilege**
   - Only grant the minimum required permissions
   - Use specific ARNs rather than wildcards where possible

2. **Regular Auditing**
   - Monitor access logs for unusual activity
   - Review permissions periodically
   - Use AWS CloudTrail for API call logging

3. **Encryption**
   - Enable S3 bucket encryption
   - Use SQS encryption in transit
   - Consider using AWS KMS for additional security

## Cost Considerations

1. **SQS Costs**
   - Standard SQS: $0.40 per million requests
   - Message storage: $0.00000040 per GB-hour

2. **S3 Costs**
   - Storage costs for log files
   - PUT/COPY/POST/LIST requests: $0.0004 per 1,000 requests
   - GET requests: $0.0004 per 10,000 requests

3. **CloudWatch Costs**
   - Standard metrics are free
   - Custom metrics: $0.30 per metric per month

## Support

For issues with the vendor setup:
1. Check AWS CloudTrail logs for API call errors
2. Verify IAM policies and permissions
3. Test with AWS CLI commands
4. Contact AWS support if needed

## Example Complete Setup Script

```bash
#!/bin/bash

# Vendor setup script
CUSTOMER_ACCOUNT_ID="123456789012"
CUSTOMER_ROLE_NAME="s3-log-replicator-lambda-execution-role"
BUCKET_NAME="vendor-logs-bucket-$(date +%s)"
QUEUE_NAME="vendor-logs-queue"
REGION="us-east-1"

echo "Setting up vendor S3 log replication..."

# Create SQS queue
echo "Creating SQS queue..."
aws sqs create-queue \
    --queue-name "$QUEUE_NAME" \
    --region "$REGION" \
    --attributes '{
        "MessageRetentionPeriod": "1209600",
        "VisibilityTimeout": "30",
        "ReceiveMessageWaitTimeSeconds": "20"
    }'

QUEUE_URL=$(aws sqs get-queue-url --queue-name "$QUEUE_NAME" --region "$REGION" --query 'QueueUrl' --output text)
QUEUE_ARN=$(aws sqs get-queue-attributes --queue-url "$QUEUE_URL" --region "$REGION" --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

# Create S3 bucket
echo "Creating S3 bucket..."
aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"

# Configure S3 notifications
echo "Configuring S3 notifications..."
aws s3api put-bucket-notification-configuration \
    --bucket "$BUCKET_NAME" \
    --region "$REGION" \
    --notification-configuration "{
        \"QueueConfigurations\": [
            {
                \"Id\": \"LogFileNotifications\",
                \"QueueArn\": \"$QUEUE_ARN\",
                \"Events\": [\"s3:ObjectCreated:*\"],
                \"Filter\": {
                    \"Key\": {
                        \"FilterRules\": [
                            {
                                \"Name\": \"suffix\",
                                \"Value\": \".log\"
                            }
                        ]
                    }
                }
            }
        ]
    }"

# Create bucket policy
echo "Creating bucket policy..."
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCustomerLambdaReadAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::$CUSTOMER_ACCOUNT_ID:role/$CUSTOMER_ROLE_NAME"
            },
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion"
            ],
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file://bucket-policy.json --region "$REGION"

# Create queue policy
echo "Creating queue policy..."
cat > queue-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCustomerLambdaSQSAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::$CUSTOMER_ACCOUNT_ID:role/$CUSTOMER_ROLE_NAME"
            },
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes"
            ],
            "Resource": "$QUEUE_ARN"
        }
    ]
}
EOF

aws sqs set-queue-attributes \
    --queue-url "$QUEUE_URL" \
    --region "$REGION" \
    --attributes "Policy=$(cat queue-policy.json | jq -c .)"

echo "Setup complete!"
echo ""
echo "Provide the following information to your customer:"
echo "SQS Queue ARN: $QUEUE_ARN"
echo "S3 Bucket Name: $BUCKET_NAME"
echo "AWS Region: $REGION"
echo ""
echo "Test the setup by uploading a .log file to s3://$BUCKET_NAME"
```

## Next Steps

1. **Deploy the setup** using the provided scripts or CloudFormation template
2. **Test the configuration** by uploading test files
3. **Provide the required information** to your customer
4. **Monitor the system** for any issues
5. **Set up alerts** for monitoring and troubleshooting 