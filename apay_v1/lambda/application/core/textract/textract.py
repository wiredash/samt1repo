import boto3
import time
import json
from trp import Document
from trp import Line 
import time
from datetime import datetime
from botocore.exceptions import ClientError
from botocore.vendored import requests
import ast
import botocore


def bucket_key_exists(bucket, key):
    s3 = boto3.resource('s3')
    try:
        s3.Object(bucket, key).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The object does not exist.
            return False
        else:
            # Something else has gone wrong.
            return False
    else:
        # The object does exist.
        return True

# def run_query(query, variables): 
#     #headers = {'Content-type': 'application/json', 'x-api-key': 'da2-p4ddwq3a4nfuxkg72u62s4nxva'}
#     headers = {'Content-type': 'application/json', 'x-api-key': 'da2-4sqho4kuyvei3nq7is7xmzzntq'}
    
#     #Calling App Sync function "InvoiceProcessingStatusV2" directly 
#     request = requests.post('https://i3xvunkeajhtje5jihgiyflqpe.appsync-api.us-east-1.amazonaws.com/graphql', json={'query': query, 'variables': variables}, headers=headers)
#     if request.status_code == 200:
#     	return request.json()
#     else:
#     	raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

def logInvoiceStatus(data): 
    headers = {'Content-type': 'application/json'}
    invoicestatusURL = 'https://czicmktc8a.execute-api.us-east-1.amazonaws.com/invoicestatus/'
    print(data) 
    request = requests.post(invoicestatusURL, json=data, headers=headers )
    if request.status_code == 200:
    	return request.json()
    else:
    	raise Exception("Query failed to run by returning code of {}.".format(request.status_code))

def log_item(jsonObj):
    print(jsonObj)
    event = jsonObj
    # invoiceID = event.get('invoiceID')
    # messageType = event.get("messageType")
    # message = event.get("message")
    # logTime = event.get("logTime")
    # bucket = event.get("bucket")
    # key = event.get("key")
    status = event.get("status")
    
#     query = '''
#     mutation CreateEvent($bucket: String, $invoiceID: String, $key: String, $logTime: String, $message: String, $messageType: String, $status: String) {
#       createInvoiceProcessingStatus(bucket: $bucket, invoiceID: $invoiceID, key: $key, logTime: $logTime, message: $message, messageType: $messageType, status: $status) {
#         id
#         bucket
#         invoiceID   
#         key
#         logTime
#         message
#         messageType
#         status
#       }
#     }    
#     '''
    
#     variables = {
#   			"bucket": bucket,
#   			"invoiceID": invoiceID,
#   			"key": key,
#   			"logTime": logTime,
#   			"message": message,
#   			"messageType": messageType,
#   			"status": status
# 		}
		
    #response = run_query(query, variables)
    
    id = 'invoice:' + event.get('invoiceID')
    data = { "invoiceId": id, "nextState": status, "stateData": jsonObj}
    
    response = logInvoiceStatus(data) 
    print(str(response))

    return {
        'statusCode': 200,
        #'body': str(response["data"])
        'body': str(response)
    }

def log_it(msg, msgtyp, invID, bucket, key, status, bufferData):
    time.ctime() 
    datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    dt = time.ctime()
    #logJson = {'id': uuidVal, 'invoiceID': invID, 'messageType': msgtyp, 'message': msg, 'logTime': dt, 'bucket': bucket, 'key': key, 'status': status}
    logJson = {'invoiceID': invID, 'bufferData': bufferData, 'messageType': msgtyp, 'message': msg, 'logTime': dt, 'bucket': bucket, 'key': key, 'status': status}
    print(logJson)
    log_item(logJson)


    
def log_it2(invID, status, bufferData,stateData):
    time.ctime() 
    datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    dt = time.ctime()
    data={} 
    #logJson = {'id': uuidVal, 'invoiceID': invID, 'messageType': msgtyp, 'message': msg, 'logTime': dt, 'bucket': bucket, 'key': key, 'status': status}
    data['bufferData']=bufferData
    data['stateData']=stateData 
    data['timestamp'] = int(time.time()) 
    logJson = {"invoiceId": 'invoice:'+invID, "nextState": status, "stateData":data}  
    response = logInvoiceStatus(logJson)
    print(str(response)) 

def startJob(s3BucketName, objectName):
    response = None
    client = boto3.client('textract')
    response = client.start_document_analysis(
    DocumentLocation={
        'S3Object': {
            'Bucket': s3BucketName,
            'Name': objectName
        }      
    },
    FeatureTypes=["TABLES"]
    )

    return response["JobId"]

def isJobComplete(jobId):
    time.sleep(5)
    client = boto3.client('textract')
    response = client.get_document_analysis(JobId=jobId)
    status = response["JobStatus"]
    print("Job status: {}".format(status))

    while(status == "IN_PROGRESS"):
        time.sleep(5)
        response = client.get_document_analysis(JobId=jobId)
        status = response["JobStatus"]
        print("Job status: {}".format(status))

    return status

def getJobResults(jobId):

    pages = []

    time.sleep(5)

    client = boto3.client('textract')
    response = client.get_document_analysis(JobId=jobId)
    
    pages.append(response)
    print("Resultset page recieved: {}".format(len(pages)))
    nextToken = None
    if('NextToken' in response):
        nextToken = response['NextToken']

    while(nextToken):
        time.sleep(5)

        response = client.get_document_analysis(JobId=jobId, NextToken=nextToken)

        pages.append(response)
        print("Resultset page recieved: {}".format(len(pages)))
        nextToken = None
        if('NextToken' in response):
            nextToken = response['NextToken']

    return pages
    
class dictObject(dict): 
  
    # __init__ function 
    def __init__(self): 
        self = dict() 
          
    # Function to add key:value 
    def add(self, key, value): 
        self[key] = value 

def check_invoice_exists(invoiceId):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('apay01')
    try:
        response = table.get_item(
            Key={
                'pk': 'invoice:'+invoiceId,
                'sk': 'v3_state:PROCESSINGCOMPLETE'
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']
        print("GetItem succeeded:")
        print(json.dumps(item))

def handler(event, context):
    # Test with this Data
    # nevent = {"statusCode": 200,"body": "{\"resultBucket\": \"apay-t-bucket\", \"resultFilename\": \"levi_converted.pdf\"}"}
    # Comment the following line during running for real
    # event = nevent
    event = json.loads(json.dumps(event))
    event = ast.literal_eval(event['body'])
    # event = json.loads(json.dumps(event))
    invetag = event["etag"].encode('utf-8').decode('unicode_escape')
    s3BucketName = event["resultBucket"]
    documentName = event["resultFilename"]
    invID = invetag
    ddbresponse = check_invoice_exists(invID)
    print(ddbresponse) 
    if ddbresponse is not None:
        return json.dumps(ddbresponse['stateData'])        
    
    if(bucket_key_exists(s3BucketName, documentName+'_'+event["etag"]+'_parsed.json')==True):
        ts = int(time.time())
        log_it('Textract Not Required, Sent for Parsing - ', 'I', invID, s3BucketName, documentName, 'PROCESSINGSKIPPED', ts)
        return {
            "statusCode": 200,
            "body": {
                "key": json.dumps(documentName+'_'+event["etag"]+'_parsed.json'),
                "bucket": s3BucketName,
                "etag" : event["etag"],
                "s3bucket" : event["s3bucket"],
                "file" : event["file"]
                }
            }
    else:


        s3 = boto3.client('s3')
        waiter = s3.get_waiter('object_exists')
        waiter.wait(Bucket=s3BucketName, Key=documentName)
        response = s3.head_object(Bucket=s3BucketName, Key=documentName)

        # invID = response['ETag'].replace('\"','')

        msg = f'Received textract invoice from {s3BucketName} and filename {documentName}'
        #log_it(msg, 'I', invID, s3BucketName, documentName, 'RECV')
        ts = int(time.time())
        # log_it(msg, 'I', invID, s3BucketName, documentName, 'PROCESSINGSTARTED', ts)
        docLines = []

        #----Start Job
        jobId = startJob(s3BucketName, documentName)

        if(isJobComplete(jobId)):
            response = getJobResults(jobId)
            vresp = response

            if(not isinstance(vresp, list)):
                rps = []
                rps.append(vresp)
                # print("Appending RPS====>", rps)
                vresp = rps

            pageCounter=0
            jsData = json.loads(json.dumps(vresp))
            for page in jsData:
                pageCounter = pageCounter+1
                for item in page['Blocks']:

                    if item['BlockType'] == "LINE":
                        docLines.append({'line': item['Text'], 'page': pageCounter, 'boundingBox': item["Geometry"]["BoundingBox"]})


        doc = Document(response)
        tableHeaders = dictObject()
        tableItems = []
        tableItem = {}

        invoiceItems = dictObject()
        invoiceMetadata = dictObject()

        #try:
        pageCnt = 0
        for page in doc.pages:

            pageCnt = pageCnt + 1
            if 1>0:

                for table in page.tables:

                    for r, row in enumerate(table.rows):
                        tableItem = {}
                        for c, cell in enumerate(row.cells):
                            #print("Table[{}][{}] = {} - Confidence - {}".format(r, c, cell.text, cell.confidence))
                            if r==0 and not cell.text is None:
                                tableHeaders.add(c, cell.text)
                            if r>0 and c in tableHeaders.keys():
                                invoiceItemKey = tableHeaders.get(c, "KeyError")

                                tableItem[invoiceItemKey] = cell.text
                        if r>0 and not tableItem is None:
                            tableItems.append(tableItem)

                    invoiceItems = tableItems

                for field in page.form.fields:
                    if not field.key is None:
                        try:
                            # invoiceMetadata.update({str(field.key): str(field.value)})
                            invoiceMetadata[str(field.key)] = str(field.value)
                        except:
                            try:
                                print("ERROR: Could not process this as String", field.value)
                                invoiceMetadata[field.key] = str(field.value)
                            except:
                                pass
                    #print("Key: {}, Value: {}".format(field.key, field.value))
                # print(type(invoiceMetadata))
                # print(json.dumps(invoiceMetadata))
                # if not invoiceMetadata is None:
                invoiceMetadata.update({'invID': invID})
                invoiceMetadata['s3BucketName'] = s3BucketName
                invoiceMetadata['documentName'] = documentName
                invoiceMetadata['etag'] = invetag

                try:
                    parserResponse = json.loads('{"invoiceLines": '+json.dumps(docLines)+',  "invID":"' + invID +'", "documentName":"'+ documentName +'", "InvoiceHeader":' + json.dumps(invoiceMetadata) + ', "InvoiceItems":'+ json.dumps(invoiceItems) +'}')
                    # print(json.dumps(parserResponse))
                except Exception as e:
                    print('Error during Invoice Sending')
                    #log_it('Error during Textract - ' + str(e), 'E', invID, s3BucketName, documentName, 'PERR')
                    log_it('Error during Textract - ' + str(e), 'E', invID, s3BucketName, documentName, 'PROCESSINGERROR')
                    return {
                        'status':400,
                        'error':{
                            'error_message' : 'Invoice could not be parsed '+str(e),
                            'details' : 'This invoice cannot be parsed by AWS Textract'
                        }
                    }

        #Now send everything to the queue

        #sqs = boto3.resource('sqs')
        #queue = sqs.get_queue_by_name(QueueName='parsedInvoiceResponse')
        #response = queue.send_message(MessageBody=json.dumps(parserResponse))
        s3 = boto3.resource("s3")
        s3.Bucket(s3BucketName).put_object(Key=documentName+'_'+event["etag"]+'_parsed.json', Body=json.dumps(parserResponse))
        #log_it('Textract Successful, Sent for Parsing - ', 'I', invID, s3BucketName, documentName, 'PSNT')
        ts = int(time.time()) 
        stateData= {
            "statusCode": 200,
            "body": {"key": json.dumps(documentName+'_'+event["etag"]+'_parsed.json'),
                "bucket": s3BucketName,
                "etag" : event["etag"],
                "s3bucket" : event["s3bucket"],
                "file" : event["file"]}
            }            
        log_it2(invID, 'PROCESSINGCOMPLETE', ts, stateData)
        return {
            "statusCode": 200,
            "body": {"key": json.dumps(documentName+'_'+event["etag"]+'_parsed.json'),
                "bucket": s3BucketName,
                "etag" : event["etag"],
                "s3bucket" : event["s3bucket"],
                "file" : event["file"]}
            }
