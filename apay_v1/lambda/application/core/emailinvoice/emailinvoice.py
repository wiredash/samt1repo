import json
import boto3
from botocore.vendored import requests
import hashlib
import datetime
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from botocore.exceptions import ClientError
import os

# Generic Exception Class
def raise_(ex):
    raise ex
    
def logInvoiceStatus(data): 
    headers = {'Content-type': 'application/json'}
    invoicestatusURL = 'https://czicmktc8a.execute-api.us-east-1.amazonaws.com/invoicestatus/'
    print(data)   
    request = requests.post(invoicestatusURL, json=data, headers=headers )
    if request.status_code == 200:
    	return request.json()
    else:
    	raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
    	
def logEmailNotification(data): 
    headers = {'Content-type': 'application/json'}
    invoicestatusURL = 'https://jy7gfk2emc.execute-api.us-east-1.amazonaws.com/emailnotification'
    request = requests.post(invoicestatusURL, json=data, headers=headers )
    if request.status_code == 200:
    	return request.json()
    else:
    	raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))    	


# def create_stripe_customer(customerName,customerDescription):
#     #Create Payment Intent for Customer
#     data = { "description": customerDescription, "name": customerName}
#     stripeCreateCustomer = requests.post('https://api.stripe.com/v1/customers', data = data,  headers={'Authorization': os.environ['stripeAPIKey']})
#         #'BEARER sk_test_vdgY12qs9qqYtBfpS9d3bdzy00m6R3LOO5'})
#     jsonResponse = json.loads(stripeCreateCustomer.text)
#     return jsonResponse['id']
    
#     try:
#         paymentIntent = jsonResponse['id']
#         clientSecret = jsonResponse['client_secret']
#     except KeyError:
#         raise Exception('payment_intent_creation_failed')    

def handler(event, context): 
    ses = boto3.client('ses')
    s3 = boto3.client('s3')
 
    msgBody = json.loads(json.dumps(event["body"]))
    # msgBody['invoiceTotal'] = '4200'   ##TEST VALUE
    customerBillTo = msgBody['customerBillTo'].replace(" ", "").lower().encode()
    hashValue = hashlib.md5(customerBillTo).hexdigest()
    print('Customer HASH value:' + hashValue)
    
    #Check if customer exists based on hash value
    customerURL = 'https://ue89tawgui.execute-api.us-east-1.amazonaws.com/customer/'
    data = { "operation": "read", "tableName": "levisCustomer", "payload": { "Key": { "id": hashValue } } }
    customerReadResponse = requests.post(customerURL, data = json.dumps(data))
    print("customerReadResponse: " + customerReadResponse.text)

# 'invoiceNumber': 
# 'customerBillTo'
# 'dueDate'
# 'description'
# 'etag'
# 'customerEmail'
# GENERATE A PAYMENT LINK FOR THE STRIPE CUSTOMER
    try:
        jsonResponse = json.loads(customerReadResponse.text)
        customerName = jsonResponse['Item']['name']
    
        try:
            customerEmail = jsonResponse['Item']['email']
            customerEmailFound = True
        except KeyError:
            raise Exception('customer_email_not_found')
        
        # try:
        #     customerStripeID = jsonResponse['Item']['stripeCustomerID']
        # except KeyError:
        #     #TODO Create Stripe Account
        #     customerDescription=hashValue
        #     customerStripeID = create_stripe_customer(customerName,customerDescription)
        #     if customerStripeID=='':
        #         raise Exception('customer_stripe_creation_failed')
    except KeyError:
            raise Exception('customer_name_not_found')
    msgBody['invoiceTotalAmount'] = msgBody['invoiceTotalAmount'].replace(".","")
    print(msgBody['invoiceTotalAmount'])
    #Create Payment Intent for Customer 
    # data = { "amount": msgBody['invoiceTotalAmount'], "currency": "CAD", "customer": customerStripeID, "metadata[invoiceID]": msgBody['invoiceNumber'], "metadata[etag]": msgBody['etag']  }
    # stripePaymentIntent = requests.post('https://api.stripe.com/v1/payment_intents', data = data,  headers={'Authorization': 'BEARER sk_test_vdgY12qs9qqYtBfpS9d3bdzy00m6R3LOO5'})
    # print("stripePaymentIntent: " + stripePaymentIntent.text)
    # jsonResponse = json.loads(stripePaymentIntent.text)
    # # 28b25e0e4cea761f43f9deee5ca2c7b5
    # try:
    #     paymentIntent = jsonResponse['id']
    #     clientSecret = jsonResponse['client_secret']
    # except KeyError:
    #     raise Exception('payment_intent_creation_failed')
    
    # dynamodb = boto3.resource('dynamodb')
    # levisInvoiceTable = dynamodb.Table('LevisInvoices')
    # levisInvoiceTable.update_item(Key={'etag': msgBody['etag']},
    #                     UpdateExpression="SET paymentIntent = :paymentIntentParam",                   
    #                     ExpressionAttributeValues={':paymentIntentParam': paymentIntent})
# {
#     TableName: "Music",
#     Key: {
#         "Artist":"No One You Know",
#         "SongTitle":"Call Me Today"
#     },
#     UpdateExpression: "SET RecordLabel = :label",
#     ExpressionAttributeValues: { 
#         ":label": "Global Records"
#     }
# }    
    
    # myClientURI = 'https://levis-demo-email-app.adaptivepay.io/index.html?'
    # paymentLink = myClientURI + 'token=' + msgBody['etag'] +'&client=' + clientSecret + '&amt=' + msgBody['invoiceTotalAmount']
    # print(paymentLink)
    
    # client = msgBody["s3bucket"]
    # #customerName = msgBody["CustomerName"] #event.get("CustomerName", "")
    # paymentLink = msgBody["PaymentLink"]
    # invoiceID = msgBody["invoiceID"]
    # invoiceIdKey = msgBody["InvoiceS3FileName"]
    bucket = msgBody["s3bucket"]
    fileName = msgBody["file"]
    # emailAddress = msgBody["EmailAddress"]
    contentType = "application/pdf"
    # # msgBody["key"]["S"]
    # print(bucket, fileName)
    data = s3.get_object(Bucket=bucket, Key=fileName)
    contents = data['Body'].read()
    
    AWS_REGION = 'us-east-1'
    BODY_TEXT = 'Invoice from Levi Strauss'
    # paymentLinkImage = '<a href={link}><img src="https://s3.us-east-2.amazonaws.com/www.adaptivebrane.com/img/stripe.png" height="25%" width="25%" /></a>'.format(link=paymentLink)
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Invoice</h1>
    <p>Please see the attached invoice.</p>
    </body>
    </html>
    """
    
    to_emails = customerEmail
    
    CHARSET = "utf-8"
    
    client = boto3.client('ses',region_name=AWS_REGION)
    
    msg = MIMEMultipart('mixed')
    msg['Subject'] = 'Invoice from Levis'
    msg['From'] = 'noreply@adaptivebrane.com'
    msg['To'] = to_emails
    
    msg_body = MIMEMultipart('alternative')
    
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)
    
    att = MIMEApplication(contents)
    att.add_header('Content-Disposition','attachment',filename=fileName)
    #att.add_header('X-SES-MESSAGE-TAGS','id=12345')
    msg.attach(msg_body)

    msg.attach(att)
    # #print(msg)
    try:
        emailResponse = client.send_raw_email(
            Source='noreply1u@adaptivebrane.com',
            Destinations=[
                to_emails
            ],
            RawMessage={
                'Data':msg.as_string(),
            },
            Tags=[
                    
                  {
                      'Name': 'invoiceIdKey',
                      'Value': msgBody['etag']
                  },
                  {
                      'Name': 'invoiceID',
                      'Value': msgBody['etag']
                  }
            ],            
            ConfigurationSetName='t1'
        )
        
        id = 'invoice:' + msgBody['etag']
        
        bufferData = 'emailNotification:' + emailResponse['MessageId']
        stateData = {
            "bufferData": bufferData
        }
        data = { "invoiceId": id, "nextState": "EMAILSENT", "stateData": stateData}
        response = logInvoiceStatus(data) 
        print(response)     
        print("email response" + str(emailResponse))
        
        # messageId = emailResponse['MessageId']
        # id = 'emailNotification:' + messageId
        # data = { "emailNotificationId": id, "nextState": "SENT", "stateData": msgBody}
        # response = logEmailNotification(data) 
        # print(response)

    except ClientError as e:
        print(e.response['Error']['Message'])
        return {
        'statusCode': 400,
        'body': json.dumps(e.response['Error']['Message'])
        }
    else:
      return {
        'statusCode': 200,
        'body': json.dumps('Email sent! MessageId = ' + emailResponse['MessageId'])
        }

