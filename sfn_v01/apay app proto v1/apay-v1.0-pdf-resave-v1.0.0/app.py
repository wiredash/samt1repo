import boto3
import json
from PyPDF2 import PdfFileMerger
from PyPDF2 import PdfFileWriter
import PyPDF2
import os


import base64
from io import BytesIO

def lambda_handler(event, context):
   
    apiCall = False
    
    #print(event)
    
    try:
        method = event['httpMethod']
        apiCall = True
    except KeyError:
        print("Cannot find http method, must be lambda Call")
        
    if apiCall == True:
        jsonStream = json.loads(event['body'])
    else:
        jsonStream = event 
        
    print(str(jsonStream))

    try:
        s3 = boto3.client('s3')
        dirpath = os.getcwd()
        print("Current directory is : " + dirpath)    
    
        os.chdir('/tmp')  
        bucket = jsonStream["s3Bucket"]
        fileName = jsonStream['fileName']
        try:
            ignorePages = 0
            ignorePages = jsonStream["ignorePages"]
        except:
            pass
        
        resultBucket = jsonStream["resultS3bucket"]
        resultFileName = jsonStream["resultFile"]
        resultPath = '/tmp/result_' + fileName
        
        path = "/tmp/" + fileName  
        
        print('Path:' + path)
        print('S3 Bucket:' + bucket)
        print('File name:' + fileName)    
        print('Result S3 Bucket:' + resultBucket) 
        print('Result File name:' + resultFileName)   
        
        data = s3.get_object(Bucket=bucket, Key=fileName)
        fileContents = data['Body'].read()

        f = open(path, 'wb')
        ret = f.write(fileContents)
        print("Number of bytes written: ")
        print(ret)    
        f.close()
        
        
        fileobj = BytesIO(fileContents)
        merger = PdfFileMerger()
        pdfFileObj = fileobj
        merger.append(fileobj = pdfFileObj, pages = (0,1))
        
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        numPages = pdfReader.numPages-ignorePages
        if numPages>2:
            merger.append(fileobj = pdfFileObj, pages = (numPages-2, numPages))
        elif pdfReader.numPages == 2:
            merger.append(fileobj = pdfFileObj, pages = (1,2))
            
        output = open(resultPath, "wb")
        merger.write(output)
        output = open(resultPath, "rb")
        s3.upload_fileobj(output, resultBucket, resultFileName)
        
        return({
            "statusCode" : 200,
            'body' : json.dumps(jsonStream)
        })  
        
    except KeyError:
        if apiCall == True:
            return {
                'statusCode': 500,
                'body': {'error' : 'Error processing file'}
            }
        else:
            raise ValueError('Error processing file')        
        
        
    