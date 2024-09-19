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
# Create client for EC2
ec2 = boto3.client('ec2')
# Create client for SSM
ssm = boto3.client('ssm')
# Create client for SNS
sns = boto3.client('sns')

# Create Lambda function handler in python
def lambda_handler(event, context):

    # Create a list of instances
    try:
        instances = ec2.describe_instances()
    except botocore.exceptions.ClientError as error:
        logger.error(error)
        raise error

    # Create empty dictionary to hold instances and actions
    taskList = {}
    taskReport = '''Actions for EC2 instances:\n'''

    for reservation in instances['Reservations']:
    #   print(reservation)
        for instance in reservation['Instances']:
            # print(instance['InstanceId'])
            newInstanceId = instance['InstanceId']
            newAction=''
            newName=''
    #        print(instance['Tags'])
            for tag in instance['Tags']:
                if tag['Key'] == 'BudgetControlAction':
                    # print(tag['Value'])
                    newAction = tag['Value']
                if tag['Key'] == 'Name':
                    # print(tag['Value'])
                    newName = tag['Value']
            if newAction != '':
                taskList[newInstanceId] = newAction
                taskReport = f"{taskReport}{newAction} for {newInstanceId} ({newName}).\n"

    # print(taskList)
    # print(taskReport)

    for task in taskList:
#    print(taskList[task])
        if taskList[task] == 'Stop':
            logger.info(f'Stopping instance {task}')
            try:
                response = ec2.stop_instances(InstanceIds=[task])
            except botocore.exceptions.ClientError as error:
                logger.error(error)
                raise error
#            print(response)
        elif taskList[task] == 'Terminate':
            logger.info(f'Terminating instance {task}')
            try:
                response = ec2.terminate_instances(InstanceIds=[task])
            except botocore.exceptions.ClientError as error:
                logger.error(error)
                raise error
#            print(response)
        else:
            logger.info(f'Informing about instance {task}')

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
            Message=taskReport,
            Subject='Budget Control actions taken'
            )
    except botocore.exceptions.ClientError as error:
        logger.error(error)
        raise error
#    print(sns_response)

    return({'HTTPStatusCode': 200}) # Is there something more interesting to return here?
