from __future__ import print_function
import json
import urllib.parse
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
import requests
from datetime import datetime
from s3logparse import s3logparse
import os
from tempfile import NamedTemporaryFile
import traceback
from aws_xray_sdk import core
core.patch_all()

import gzip
from base64 import b64decode
from requests_aws4auth import AWS4Auth



# Notes:
# https://docs.aws.amazon.com/code-samples/latest/catalog/python-s3-get_object.py.html
# https://forums.aws.amazon.com/thread.jspa?threadID=221549
# https://stackoverflow.com/questions/32000934/python-print-a-variables-name-and-value
# https://pypi.org/project/s3-log-parse/
# https://www.geeksforgeeks.org/python-dictionary/
# https://stackoverflow.com/questions/44381249/treat-a-string-as-a-file-in-python
# https://github.com/elastic/elasticsearch-py
# https://docs.aws.amazon.com/lambda/latest/dg/running-lambda-code.html


print('Loading function')

##################################################################################################
# Initialize boto3 client at global scope for connection reuse
#  Get environment variables for reuse
##################################################################################################
client = boto3.client('ssm')
s3 = boto3.client('s3')

host = os.environ.get('ES_ENDPOINT')
index = os.environ.get('ES_INDEX')
region = os.environ.get('ES_REGION')



##################################################################################################
# Helper functions to process incoming decoded and compressed event from CloudWatch Logs
##################################################################################################
def decompress(data) -> bytes:
    return gzip.decompress(data)

def decode_record(data: dict) -> dict:
    x = decompress(b64decode(data['data']))
    return json.loads(x.decode('utf8'))

def decode_event(event: dict) -> dict:
    return decode_record(event['awslogs'])


##################################################################################################
# AWS Lambda hander invoked first
##################################################################################################
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))



    ######################################################################
    # Get all parameters containing credentials for this app
    #   If not -> user credentials from environment variables
    ######################################################################
    parent_stack_name = os.getenv('parent_stack_name')
    try:
        param_name = '/' + parent_stack_name + '/cloud_id'
        param_details = client.get_parameter(Name=param_name,WithDecryption=True)
        if 'Parameter' in param_details and len(param_details.get('Parameter')) > 0:
            parameter = param_details.get('Parameter')
            cloud_id = parameter.get('Value')
            # log.info('cloud_id=' + cloud_id)

        param_name = '/' + parent_stack_name + '/http_auth_username'
        param_details = client.get_parameter(Name=param_name,WithDecryption=True)
        if 'Parameter' in param_details and len(param_details.get('Parameter')) > 0:
            parameter = param_details.get('Parameter')
            http_auth_username = parameter.get('Value')
            # log.info('http_auth_username=' + http_auth_username)
        
        param_name = '/' + parent_stack_name + '/http_auth_password'
        param_details = client.get_parameter(Name=param_name,WithDecryption=True)
        if 'Parameter' in param_details and len(param_details.get('Parameter')) > 0:
            parameter = param_details.get('Parameter')
            http_auth_password = parameter.get('Value')
            # log.info('http_auth_password=' + http_auth_password)

        param_name = '/' + parent_stack_name + '/index_name'
        param_details = client.get_parameter(Name=param_name,WithDecryption=True)
        if 'Parameter' in param_details and len(param_details.get('Parameter')) > 0:
            parameter = param_details.get('Parameter')
            index_name = parameter.get('Value')
            # log.info('index_name=' + index_name)

    except:
        # log.debug("Encountered an error loading credentials from SSM.")
        traceback.print_exc()
        cloud_id = os.getenv('cloud_id')
        http_auth_username = os.getenv('http_auth_username')
        http_auth_password = os.getenv('http_auth_password')
        index_name = os.getenv('index_name')
        

    ##################################################################################################
    #Now put that data in ElasticCloud! 
    ##################################################################################################
    # es = elastic_client
    es = Elasticsearch(cloud_id=cloud_id, http_auth=(http_auth_username, http_auth_password))
    es.info()

    # create an index in elasticsearch, ignore status code 400 (index already exists)
    es.indices.create(index=index_name, ignore=400)
    # {'acknowledged': True, 'shards_acknowledged': True, 'index': 'my-index'}
    # datetimes will be serialized
    # es.index(index="my-index", id=44, body={"any": "data44", "timestamp": datetime.now()})
    
    # Based on: 
    # https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-aws-integrations.html#es-aws-integrations-dynamodb-es
    print(event)
    print("\n\n event=" + json.dumps(event))
    event = decode_event(event)
    print(json.dumps(event))

    logEvents = event['logEvents']
    print("Log events:\n{}".format(logEvents))

    count = 0
    errors = 0
    print('Processing records...')
    for record in logEvents:
        id = record['id']
        document = json.loads(record['message'])
        res = es.index(index=index_name, body=document)
        print(res)
        print("\n\n result=" + res['result'])
        # r = requests.put(url + id, auth=awsauth, json=document, headers=headers)
        # if (res['status_code'] > 299):
        if (res['result'] == 'created'):
            count += 1
        else:
            print('Failed to post \ndocument:{0} \nrecord id:{1} \nresult:{2}:\n'.format(document, id, res['result']))
            errors = 0
    print('{} records posted to Elasticsearch in ElasticCloud.'.format(count))
    if (errors > 0):
        print('{} failed records not posted to Elasticsearch in ElasticCloud.'.format(count))


    # es_body={
    # "bucket_owner": log_entry.bucket_owner,
    # "bucket": log_entry.bucket,
    # "timestamp": log_entry.timestamp,
    # "remote_ip": log_entry.remote_ip,
    # "requester": log_entry.requester,
    # "request_id": log_entry.request_id,
    # "operation": log_entry.operation,
    # "s3_key": log_entry.s3_key,
    # "request_uri": log_entry.request_uri,
    # "status_code": log_entry.status_code,
    # "error_code": log_entry.error_code,
    # "bytes_sent": log_entry.bytes_sent,
    # "object_size": log_entry.object_size,
    # "total_time": log_entry.total_time,
    # "turn_around_time": log_entry.turn_around_time,
    # "referrer": log_entry.referrer,
    # "user_agent": log_entry.user_agent,
    # "version_id": log_entry.version_id
    # }

    # es.index(index=index_name, body=es_body)



