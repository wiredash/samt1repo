import json

def handler(event, context):
    return {
        "statusCode": 500,
        "body": json.dumps('Invoice Processing needs Customer Email to continue! Process Halted')
    }
   