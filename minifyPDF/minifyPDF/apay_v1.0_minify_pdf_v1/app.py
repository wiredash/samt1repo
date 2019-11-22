import json
from PyPDF2 import PdfFileMerger
import PyPDF2

def pdfMinify(file):
    merger = PdfFileMerger()
    pdfFileObj = open('916264.pdf', 'rb')
    merger.append(fileobj = pdfFileObj, pages = (0,1))

    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    if pdfReader.numPages>2:
        merger.append(fileobj = pdfFileObj, pages = (pdfReader.numPages-2, pdfReader.numPages))
    elif pdfReader.numPages == 2:
        merger.append(fileobj = pdfFileObj, pages = (1,2))

    # Write to an output PDF document
    output = open("document-output.pdf", "wb")
    merger.write(output)    

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

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
