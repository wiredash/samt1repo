import json
import logging
import boto3
from botocore.exceptions import ClientError

class MessageMalformed(Exception): pass

def bucket_contents(bucketname):
    s3 = boto3.resource('s3')
    return s3.Bucket(bucketname)

def list_s3_objects(bucketname):
    s3_client = boto3.client("s3")   
    try:
        response = s3_client.list_objects_v2(Bucket=bucketname)
    except ClientError as e:
        # AllAccessDisabled error == bucket not found
        logging.error(e)
        return None

    # Only return the contents if we found some keys
    if response['KeyCount'] > 0:
        return response['Contents']

    return None     

def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    qpmBucket = event['queryStringParameters']['bucket']
    fn_bucket = list_s3_objects(qpmBucket)
    print(fn_bucket)
    
    
    return {
        "statusCode": 200,
        "body": json.dumps(str(fn_bucket)),
    }
