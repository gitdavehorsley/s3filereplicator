import json
import boto3
import os
import logging
from botocore.exceptions import ClientError
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to process SQS messages and copy S3 objects
    
    Args:
        event: SQS event containing messages
        context: Lambda context
        
    Returns:
        Dict containing success and error counts
    """
    logger.info(f"Processing {len(event.get('Records', []))} SQS messages")
    
    success_count = 0
    error_count = 0
    
    for record in event.get('Records', []):
        try:
            # Parse SQS message body (S3 notification)
            message_body = json.loads(record['body'])
            
            # Handle S3 notification format
            if 'Records' in message_body:
                for s3_record in message_body['Records']:
                    if s3_record.get('eventSource') == 'aws:s3':
                        bucket_name = s3_record['s3']['bucket']['name']
                        object_key = s3_record['s3']['object']['key']
                        
                        # Copy the object
                        copy_s3_object(bucket_name, object_key)
                        success_count += 1
            else:
                # Direct S3 event format
                bucket_name = message_body.get('bucket', {}).get('name')
                object_key = message_body.get('object', {}).get('key')
                
                if bucket_name and object_key:
                    copy_s3_object(bucket_name, object_key)
                    success_count += 1
                else:
                    logger.warning(f"Unexpected message format: {message_body}")
                    error_count += 1
                    
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_count += 1
            continue
    
    logger.info(f"Processing complete. Success: {success_count}, Errors: {error_count}")
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success_count': success_count,
            'error_count': error_count
        })
    }


def copy_s3_object(source_bucket: str, source_key: str) -> None:
    """
    Copy an S3 object from source bucket to destination bucket
    
    Args:
        source_bucket: Name of the source S3 bucket
        source_key: Key of the object to copy
    """
    destination_bucket = os.environ['DESTINATION_BUCKET']
    
    try:
        logger.info(f"Copying s3://{source_bucket}/{source_key} to s3://{destination_bucket}/{source_key}")
        
        # Copy object
        copy_source = {
            'Bucket': source_bucket,
            'Key': source_key
        }
        
        s3_client.copy_object(
            CopySource=copy_source,
            Bucket=destination_bucket,
            Key=source_key,
            MetadataDirective='COPY'
        )
        
        logger.info(f"Successfully copied {source_key}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            logger.warning(f"Object {source_key} not found in source bucket")
        else:
            logger.error(f"Error copying {source_key}: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error copying {source_key}: {str(e)}")
        raise


def validate_s3_notification(message_body: Dict[str, Any]) -> bool:
    """
    Validate that the message body contains valid S3 notification data
    
    Args:
        message_body: Parsed JSON message body
        
    Returns:
        True if valid, False otherwise
    """
    if 'Records' in message_body:
        for record in message_body['Records']:
            if (record.get('eventSource') == 'aws:s3' and 
                's3' in record and 
                'bucket' in record['s3'] and 
                'object' in record['s3']):
                return True
    elif ('bucket' in message_body and 
          'object' in message_body and 
          message_body['bucket'].get('name') and 
          message_body['object'].get('key')):
        return True
    
    return False 