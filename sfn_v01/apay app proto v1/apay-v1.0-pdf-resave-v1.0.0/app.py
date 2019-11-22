import json
import subprocess
from subprocess import Popen
import os
import sys
import boto3
import glob
import base64
from io import BytesIO
from PyPDF2 import PdfFileMerger
import PyPDF2
# import requests


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    pdf64 = event["body"]

    # Need this line as it does 'b'b'pdfdatacontent'.
    # pdf64 = pdf64[2:].encode('utf-8')

    # buffer = BytesIO()
    content = base64.b64decode(pdf64)

    fileobj = BytesIO(content)
    # newfile = BytesIO()
    merger = PdfFileMerger()
    pdfFileObj = fileobj
    merger.append(fileobj = pdfFileObj, pages = (0,1))
    
    output = open("/tmp/document-output.pdf", "wb")
    merger.write(output)
    kk = open("/tmp/document-output.pdf", "rb")
    pdfdata = kk.read()
    # content = base64.b64decode(pdfFileObj)
    # fileobj = BytesIO(pdfFileObj)
    s3.upload_fileobj(kk, 'apay-levis-invoice-master-out', '_3tmp.pdf')
    
    # dirpath = os.getcwd()
    # print("Current directory is : " + dirpath)      
    # os.chdir('/tmp') 
    # s3 = boto3.client('s3') 
    # fileName = '916266_T.pdf'
    # path = "/tmp/" + fileName 
    # data = s3.get_object(Bucket="apay-levis-invoice-master-in", Key="916264.pdf")
    # contents = data['Body'].read()
    # f = open(path, 'wb')
    # ret = f.write(str(contents))
    # print("Number of bytes written: ")
    # print(ret)    
    # f.close()

    # p = Popen([path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    # output, errors = p.communicate()
    # print("Error: " + errors)
    # print("Output: " + output)    
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

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e
    pdfdata = str(base64.b64encode(pdfdata))
    # pdfdata = pdfdata[2:].encode('utf-8')

    return {
        "statusCode": 200,
        "headers": {"Content-type" : "application/pdf"},
        "isBase64Encoded": "true",
        "body":pdfdata
        }
    
