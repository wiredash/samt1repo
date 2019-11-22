import json
import boto3
import hashlib
import requests
from decimal import *

def logInvoiceStatus(data): 
    headers = {'Content-type': 'application/json'}
    invoicestatusURL = 'https://czicmktc8a.execute-api.us-east-1.amazonaws.com/invoicestatus/'
    request = requests.post(invoicestatusURL, json=data, headers=headers )
    if request.status_code == 200:
    	return request.json()
    else:
    	raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))




def handler(event, context):
    try:
        event = event["body"]
    except KeyError:
        pass
        #do nothing, allows for local testing
        
    print("etag:" + event["etag"])
    #dynamodb = boto3.resource('dynamodb')
    #table = dynamodb.Table('LevisInvoices')
    id = event["etag"]
    try:
        customerBillTo = event["customerBillTo"]
        customerName = event["customerBillTo"]
        invoiceId= 'invoice:'+event["etag"]
        customerBillTo = customerBillTo.replace(" ", "").lower().encode()
        hashValue = hashlib.md5(customerBillTo).hexdigest()
        print('Customer HASH value:' + hashValue)
        
        #Check if customer exists based on hash value
        customerURL = 'https://ue89tawgui.execute-api.us-east-1.amazonaws.com/customer/'
        data = { "operation": "read", "tableName": "levisCustomer", "payload": { "Key": { "id": hashValue } } }
        customerReadResponse = requests.post(customerURL, data = json.dumps(data))
        
        print("customerReadResponse: " + customerReadResponse.text)
        
        customerFound = False
        customerEmailFound = False
        try:
            jsonResponse = json.loads(customerReadResponse.text)
            customerId = jsonResponse['Item']['id']
            customerName = jsonResponse['Item']['name']
            customerFound = True
            try:
                customerEmail = jsonResponse['Item']['email']
                customerEmailFound = True
            except KeyError:
                print('Customer email not found')

        except KeyError:
            print('Customer not found')
            
        if customerFound == False:
            print("CustomerName: " + customerName)
            data = { "operation": "create", "tableName": "levisCustomer", "payload": {"Item": { "id": str(hashValue), "name": customerName }} }
            customerCreateResponse = requests.post(customerURL, data = json.dumps(data))
            print("customerCreateResponse" + customerCreateResponse.text)
            
        if customerEmailFound == True:
            print("customerEmail: " + customerEmail)
            event['customerEmail'] = customerEmail
            data = { "invoiceId": invoiceId, "nextState": "CUSTOMERASSIGNED", "stateData": {'bufferData' : customerId}}
            response = logInvoiceStatus(data) 
            print(str(response))
        else:
            event['customerEmail'] = ""
            #print('Customer email not found')
            #event['customerEmail'] = 'contact@adaptivebrane.com'
            data = { "invoiceId": invoiceId, "nextState": "CUSTOMERASSIGNMENTERROR", "stateData": {'bufferData' : 'Retry'}}
            response = logInvoiceStatus(data) 
            print(str(response))

        print('body: ' + str(event))
        # table.put_item(
        #     Item={
        #         'etag' : id,
        #         'body': event
        #     }
        # )
        
        invoiceId = 'invoice:' + id
        stateData = {}
        customerId='customer:'+customerId 
        stateData['bufferData'] = customerId 
        stateData['stateData'] = event
        data = { "invoiceId": invoiceId, "nextState": "CREATED", "stateData": stateData}

        
        ##      CREATE CUSTOMER BALANCE     
        # data = { "operation": "update", "tableName": "levisCustomer", "payload": {"Item": { "id": str(hashValue), "name": customerName }} }
        # customerCreateResponse = requests.post(customerURL, data = json.dumps(data))
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('apay01')
        
        invoiceExists = table.get_item(Key={"pk": invoiceId, "sk": "v5_state:CREATED"}) 
        print(invoiceExists)
        if "Item" in invoiceExists:
            table.update_item(
                Key={
                    'pk': customerId,
                    'sk': 'balance'
                },
                UpdateExpression="SET bufferData = :bufferData, amount = if_not_exists(amount, :start) + :inc",
            
                ExpressionAttributeValues={ 
                    ':bufferData': 'CAD',  
                    ':inc': Decimal(event['invoiceTotalAmount']),
                    ':start': 0,
                },
                ReturnValues="UPDATED_NEW"
            )
        response = logInvoiceStatus(data) 
        print(str(response))  
        responseStream = event
        # del responseStream['invoiceItems']
        
        return {
            "statusCode": 200,
            "body": responseStream
        }
    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "body": {'error': json.dumps(str(e))}
        }