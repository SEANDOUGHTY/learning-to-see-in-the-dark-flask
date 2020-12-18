from app import app
import cv2
import math
import numpy as np
from PIL import Image
import boto3
import logging
import os

def allowed_file(filename, extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions


def predict(image, ratio):        
    im = importImage(image, ratio)
    
    app.logger.info("Transforming Image")
    im = inferTransform(im)
    
    app.logger.info("Loading Input Image to %s" % device)
    tensor = torch.from_numpy(im).transpose(0, 2).unsqueeze(0)
    tensor = tensor.to(device)

    with torch.no_grad():    
        # Inference
        app.logger.info("Performing Inference on Input Image")
        try:
            output = model(tensor)
        except:
            app.logger.error("Inference Failed")
            return "Image Inference failed"
        
        # Post processing for RGB output
        output = output.to('cpu').numpy() * 255
        output = output.squeeze()
        output = np.transpose(output, (2, 1, 0)).astype('uint8')
        output = Image.fromarray(output).convert("RGB")

    return output

def check_instance():
    logging.info("Checking for EC2 instances")
    client = boto3.client('ec2',
        region_name = os.environ['AWS_REGION'])
    response = client.describe_instances(
    Filters=[
        {
            'Name': 'subnet-id',
            'Values': ['subnet-0d6e5384d0fb5b377']
        },
        {
            'Name': 'instance-state-name',
            'Values': ['pending', 'running']
        }
    ],
    MaxResults=5
)
    logging.info("Located %d instances" % len(response["Reservations"]))

    if len(response["Reservations"]) >= 1:
        return True
    else: return False

def launch_instance(session):
    ec2 = session.resource('ec2')
    logging.info("Launching 1 EC2 instance")
    instance = ec2.create_instances(
    MaxCount=1,
    MinCount=1,
    ImageId='ami-03ba6b1cc8dbf7a93',
    InstanceType='t2.medium',
    SecurityGroupIds=['sg-077764cc5a36ca83b'],
    SubnetId='subnet-0d6e5384d0fb5b377',
    InstanceInitiatedShutdownBehavior='terminate',
    LaunchTemplate={
        'LaunchTemplateName': 'learningtoseeinthedark',
        'Version': '5'
    },
    InstanceMarketOptions={
        'MarketType': 'spot',
        'SpotOptions': {}
    },
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [{
            'Key': 'name', 
            'Value': 'learningtoseeinthedark'
        }]
        }]
)

def add_queue(fileName, ratio):
    sqs = boto3.client('sqs',
        region_name = os.environ['AWS_REGION'])
    logging.info("Adding job to SQS")
    queue_url = 'https://sqs.us-east-1.amazonaws.com/195691282245/learningtoseeinthedark'
    response = sqs.send_message(
    QueueUrl=queue_url,
    MessageAttributes={
        'Title': {
            'DataType': 'String',
            'StringValue': 'NewTask'
        },
        'Author': {
            'DataType': 'String',
            'StringValue': 'Sean Doughty'
        },
    },
    MessageBody=('%s, %d' % (fileName, ratio))
)
    return (response['MessageId'])

