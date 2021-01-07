from app import app
from flask import Flask, request, Response, send_file, make_response
from flask_api import status
import requests
from app.utils import *
from PIL import Image
import boto3
import io
import os
import time
from flask_cors import CORS, cross_origin

# Allowed image inputs
ALLOWED_EXTENSIONS = {'png'}
LIMIT = 5 # max number of requests
RESET = 3600 # reset frequency in seconds

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

@app.route('/', methods=['GET'])
def health_check():
    app.logger.info("Performing health check")
    return "Server Healthy", status.HTTP_200_OK

@app.route('/upload', methods=['POST'])
@cross_origin(supports_credentials=True)
def upload():
    if request.method == 'POST':
        if not request.cookies.get('requests'):
            num_requests = 0
        else:
            num_requests = int(request.cookies.get('requests'))
            if num_requests >= 5:
                last_reset = float(request.cookies.get('last_reset'))
                if (time.time()-last_reset) > RESET:
                    num_requests = 0
                else:
                    return "Too many requests", status.HTTP_429_TOO_MANY_REQUESTS

        app.logger.info(num_requests)
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
        
        res = make_response(str('output_' + filename[6:]))
        res.set_cookie('requests', str(num_requests+1))
        if num_requests == 0:
            res.set_cookie('last_reset', str(time.time()))
        return res, status.HTTP_200_OK
    
    return "Bad Request", status.HTTP_400_BAD_REQUEST
       
@app.route('/download', methods=['GET'])
@cross_origin()
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

@app.route('/checkinstance', methods=['GET'])    
@cross_origin()
def checkinstance():
    if request.method == 'GET':
        if not check_instance():
            launch_instance(session)
            return "Launching Instance", status.HTTP_200_OK
        return  "Instance running", status.HTTP_200_OK

    return "Bad Request", status.HTTP_400_BAD_REQUEST

@app.route('/debug', methods=['GET'])
def debug():
    if request.method == 'GET':
        res = make_response('output_222')
        res.set_cookie('requests', '1')
        res.set_cookie('last_reset', str(time.time()))
        return res, status.HTTP_200_OK
