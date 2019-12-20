# Purpose

Provide an example of streaming S3 object-level logs from CloudTrail to Elasticsearch.

## How it works

1. Configure CloudTrail to log S3 data access events to CloudWatch log group. 
2. Subscribe Lambda to CloudWatch log group. 
3. Lambda receive(s) event(s), makes an API put request to Elasticsearch

## Pre-requisites

1. You need an existing Amazon Elasticsearch cluster running in an existing VPC. 
This should work with a non-Amazon Elasticsearch cluster too, but you may need
to tweak the CloudFormation template and/or Lambda function a bit. 

2. Install the AWS CLI

3. Install the AWS SAM CLI

## Cost

This template enables logging on all buckets within the template's launch region. 
Depending on the level of your S3 activity, you could potentially generate a 
signficant amount of log data, which has both cost and performance considerations.

You may want to initially adjust the demo to only apply to certain lower-volume
buckets and/or object filters. 

## Deployment

1. Git clone this repository

    `git clone...`

2. Open `deploy.sh` and edit the values below: 

    ```sh
    # deploy.sh
    BUCKET=<EXISTING_BUCKET_FOR_DEPLOYMENT_ARTIFACTS>
    ES_DOMAIN_NAME=<DOMAIN_NAME_OF_YOUR_ES_CLUSTER>
    ES_ENDPOINT=<HTTPS_ENDPOINT_OF_YOUR_ES_CLUSTER>
    ```
