#!/bin/bash

# EDIT THESE VALUES
BUCKET=<EXISTING_BUCKET_FOR_DEPLOYMENT_ARTIFACTS>   # this is any bucket where the SAM CLI can deploy your CF artifacts
ES_DOMAIN_NAME=<DOMAIN_NAME_OF_YOUR_ES_CLUSTER>     # this is the "domain name" you see in the elasticsearch console
ES_ENDPOINT=<HTTPS_ENDPOINT_OF_YOUR_ES_CLUSTER>

# DO NOT EDIT BELOW (unless you want to)
STACK_NAME=s3-events-to-es

# Install Lambda function dependencies
sam build

if [ $? -ne 0 ]; then
    echo "SAM build failed"
fi

sam package \
    --s3-bucket $BUCKET \
    --template-file .aws-sam/build/template.yaml \
    --output-template-file packaged.yaml

if [ $? -ne 0 ]; then
    echo "SAM package failed"
fi

sam deploy \
    --template-file packaged.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides EsDomainName=$ES_DOMAIN_NAME EsEndpoint=$ES_ENDPOINT
  
if [ $? -ne 0 ]; then
    echo "SAM deployment failed"
fi