#./xpsconvert -o levi2.pdf levi.xps
#./pdf2xps -o levi.xps  levi.pdf

import subprocess
from subprocess import Popen
import json
import os
import sys
import boto3
import glob

def handler(event, context):
    
    dirpath = os.getcwd()
    print("Current directory is : " + dirpath)    
    
    os.chdir('/tmp')    
    s3 = boto3.client('s3')    
    bucket = event.get("s3bucket", "apay-t-bucket")
    etag = event.get("etag", "")
    fileName = event.get("file", "levi.pdf")  
    resultBucket = event.get("resultS3bucket", bucket)
    fileNameWithoutExt = os.path.splitext(fileName)[0]
    defaultResultFileName = fileNameWithoutExt + "_converted.pdf"
    resultFileName = event.get("resultFile", defaultResultFileName) 
    data = s3.get_object(Bucket=bucket, Key=fileName)
    contents = data['Body'].read()
    
    if bucket == resultBucket:
        print("Source bucket cannot be the same as target bucket")
        return    
    
    xpsFilePath = "/tmp/" + fileNameWithoutExt + ".xps"
    path = "/tmp/" + fileName   
    print('Path:' + path)
    print('S3 Bucket:' + bucket)
    print('File name:' + fileName)    
    print('Result S3 Bucket:' + resultBucket) 
    print('Result File name:' + resultFileName)    
    
    f = open(path, 'wb')
    ret = f.write(contents)
    print("Number of bytes written: ")
    print(ret)    
    f.close()
      
    print(glob.glob("/tmp/*"))    
    
    p = Popen(["pdf2xps", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    output, errors = p.communicate()
    print("Error: " + errors)
    print("Output: " + output)
        
    p = Popen(["xpsconvert", xpsFilePath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)    
    
    output, errors = p.communicate()
    print("Error: " + errors)
    print("Output: " + output)
    
    if not errors:
        s3.upload_file(path, resultBucket, resultFileName)   
        
        bucket = event.get("s3bucket", "apay-t-bucket")
        etag = event.get("etag", "")
        fileName = event.get("file", "levi.pdf")  
        
        result = {'etag' : etag, 's3bucket' : bucket, 'file' : fileName, 'resultBucket': resultBucket, 'resultFilename': resultFileName}
               
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }   
    else:
        return {
            'statusCode': 500,
            'body': errors
        }           
        
