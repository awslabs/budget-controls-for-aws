# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Load dependencies
import boto3
import botocore
import json
import logging  

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

### Create Boto3 clients
# Create client for SSM
ssm = boto3.client('ssm')
# Create client for SNS
sns = boto3.client('sns')
# Create client for EC2
ec2 = boto3.client('ec2')

# Create Lambda function handler in python
def lambda_handler(event, context):
    # print(event)

    # Is the resource an EC2 instance
    if (event['detail']['resourceType'] == 'AWS::EC2::Instance'):
    
        instanceId = event['detail']['resourceId']
        resourceType = 'EC2 instance'
    
        try:
            tag_response = ec2.create_tags(
                Resources=[
                    instanceId,
                ],
                Tags=[
                    {
                        'Key': 'BudgetControlAction',
                        'Value': 'Inform',
                    },
                ],
            )
        except botocore.exceptions.ClientError as error:
            logger.error(error)
            raise error
#    print(tag_response)
    logger.info(f"Resetting BudgetControlAction tag to \"Inform\" for {resourceType} {instanceId}.")
    
    remediationReport = f'''Remediation for {resourceType} {instanceId}:
        A tag called BudgetControlAction has been added to this resource.  The value has been set to \"Inform\".
        Other valid values are \"Stop\" and \"Terminate\" and are case-sensitive.  This determines the action that 
        will be taken when your Budget is reached.  You must update this tag to change the action.'''
    
    # Query SSM Parameter Store for the SNS Alert topic
    try:
        ssm_response = ssm.get_parameter(Name='BudgetControlSNSAlertTopic')
    except botocore.exceptions.ClientError as error:
        logger.error(error)
        raise error
#    print(ssm_response)
    
     # Send the report via SNS
    try:
        sns_response = sns.publish(
            TopicArn = ssm_response['Parameter']['Value'],
            Message=remediationReport,
            Subject='Budget Control remediation report'
            )
    except botocore.exceptions.ClientError as error:
        logger.error(error)
        raise error
#    print(sns_response)

    return({'HTTPStatusCode': 200}) # Is there something more interesting to return here?