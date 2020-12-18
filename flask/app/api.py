from app import app
from flask import Flask, request, Response, send_file
from flask_api import status
import requests
from app.utils import *
from PIL import Image
import boto3
import io
import os
import time

# Allowed image inputs
ALLOWED_EXTENSIONS = {'png'}

# AWS Session Setup
app.logger.info("Creating AWS Session")
try:
    session = boto3.Session(
    aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name = os.environ['AWS_REGION']
    )
except:
    app.logger.error("AWS Session Failed: Check Access Key and Permissions")

app.logger.info("Server Ready")

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        app.logger.info("Image upload recieved")
        if 'image' not in request.files:
            app.logger.error("No image attached")
            return "No image attached", status.HTTP_400_BAD_REQUEST
        input_image = request.files['image']
        ratio = float(request.form["ratio"])

        # if user does not select file
        app.logger.info("checking image format")
        if input_image.filename == '':
            app.logger.error("No selected file")
            return "No selected file", status.HTTP_400_BAD_REQUEST
        if input_image and allowed_file(input_image.filename, ALLOWED_EXTENSIONS):
            filename = "input_%d" % time.time()
        else:
            app.logger.error("Invalid file type")
            return "Invalid file type", status.HTTP_400_BAD_REQUEST
        
        app.logger.info("Uploading image to S3")
        bucketName = "pyseedarkresources"

        try:
            s3 = session.resource('s3')
            s3.Bucket(bucketName).put_object(
                Key="inputs/%s" % filename,
                Body=input_image,
                ContentType='image/png',
            )
        except:
            app.logger.error("Failed to Upload Image")
            return "Failed to Upload Image", status.HTTP_400_BAD_REQUEST

        add_queue(filename, ratio)
        if not check_instance():
            launch_instance(session)
        
        return 'output_' + filename[6:], status.HTTP_200_OK
    
    return "Bad Request", status.HTTP_400_BAD_REQUEST
       
@app.route('/download', methods=['GET'])
def download():
    if request.method == 'GET':
        fileName = 'outputs/' + request.args['fileName']
        app.logger.info("Recieved Download Request for %s" % fileName)

        bucketName = "pyseedarkresources"
        try:
            s3 = session.resource('s3')
            object = s3.Object(bucketName, fileName)
            
            image = io.BytesIO()
            object.download_fileobj(image)
            image.seek(0)
        except:
            logging.info("Image Not Ready")
            if not check_instance():
                launch_instance(session)
            return "Not ready", status.HTTP_404_NOT_FOUND
              
        return send_file(image, mimetype='image/png'), status.HTTP_200_OK

    return "Bad Request", status.HTTP_400_BAD_REQUEST