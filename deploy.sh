#!/bin/bash

BUCKET=<EXISTING_BUCKET_FOR_DEPLOYMENT_ARTIFACTS>
STACK_NAME=s3-events-to-es

# Install Lambda function dependencies
sam build

sam package \
    --s3-bucket $BUCKET \
    --template-file .aws-sam/build/template.yaml \
    --output-template-file packaged.yaml

sam deploy \
    --template-file packaged.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM
  
