import os, json, boto3
from dotenv import load_dotenv
from urllib.parse import unquote_plus

load_dotenv()

rdsd = boto3.client("rds-data")
s3 = boto3.client("s3")
DB_ARN     = os.environ["DB_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DB_NAME    = os.environ["DB_NAME"]

def lambda_handler(event, context):
    '''
    Main Lambda handler function to preprocess the power level and save it to Aurora RDS
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    '''
    
    for rec in event.get("Records", []):
        bucket = rec['s3']['bucket']['name']
        key = unquote_plus(rec['s3']['object']['key'])
        
        obj = s3.get_object(Bucket=bucket, key=key)
        body = obj['Body'].read()
        match_timeline_json = json.loads(body)
        print(match_timeline_json)
        
        # res = rdsd.execute_statement(
        #     resourceArn=DB_ARN,
        #     secretArn=SECRET_ARN,
        #     database=DB_NAME,
        #     sql="SELECT now()"
        # )
        