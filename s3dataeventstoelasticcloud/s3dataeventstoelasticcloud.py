from __future__ import print_function
import json
import urllib.parse
import boto3
from elasticsearch import Elasticsearch
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


# Initialize boto3 client at global scope for connection reuse
client = boto3.client('ssm')
s3 = boto3.client('s3')




# awsauth = AWS4Auth(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, 'es', session_token=AWS_SESSION_TOKEN)
host = os.environ.get('ES_ENDPOINT')
index = os.environ.get('ES_INDEX')
region = os.environ.get('ES_REGION')

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
HOSTS=[{'host': host, 'port': 443}]
elastic_client = Elasticsearch(
    hosts=HOSTS,
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)




def decompress(data) -> bytes:
    return gzip.decompress(data)

def decode_record(data: dict) -> dict:
    x = decompress(b64decode(data['data']))
    return json.loads(x.decode('utf8'))

def decode_event(event: dict) -> dict:
    return decode_record(event['awslogs'])



def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))



##################################################################################################
    #Now put that data in ElasticCloud! 
##################################################################################################
    es = elastic_client
    # es = Elasticsearch(cloud_id=cloud_id_var, http_auth=(http_auth_username,http_auth_password))
    es.info()

    # create an index in elasticsearch, ignore status code 400 (index already exists)
    es.indices.create(index='access-logs', ignore=400)
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



