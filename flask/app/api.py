from app import app
from flask import Flask, request, Response
import torch
import rawpy
from src.model.model import UNet
from app.utils import inferTransform, importImage
import numpy as np
from PIL import Image
import boto3
import io
import os

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

# Setting Device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') 
app.logger.info("Set torch device as: %s" % device)

# Load model
app.logger.info ("Loading UNet Model to %s"% device)
try:
    checkpoint_path = 'checkpoint/checkpoint.t7'
    model = UNet().to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device)["state_dict"])
except:
    app.logger.error("Model Unsuccessfully Loaded")


#set model to evaluate mode
model.eval()

@app.route('/', methods=['POST'])
def predict():
    if request.method == 'POST':
        # Retrieving Data from POST request
        data = request.get_json()
        bucketName = data['Bucket']
        inputImage = data['input-image']
        outputImage = data['output-image']
        ratio = int(data['ratio'])
        
        app.logger.info("POST Request Recieved; inputImage: %s, outputImage: %s, ratio %d" % (inputImage, outputImage, ratio))
        
        app.logger.info("Downloading Input Image from S3")
        try:
            s3 = session.resource('s3')
            object = s3.Object(bucketName, inputImage)
            
            image = io.BytesIO()
            object.download_fileobj(image)
            image.seek(0)
        except:
            app.logger.error("Unable to Download Input Image from S3")
            return "Unable to Download Input Image from S3"

        app.logger.info("Importing Image from: %s" % inputImage)
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
            #output.show()

            # Output buffer for upload to S3
            buffer = io.BytesIO()            
            output.save(buffer, "PNG")
            buffer.seek(0) # rewind pointer back to start

            app.logger.info("Uploading Image to %s", outputImage)
            try:
                s3.Bucket(bucketName).put_object(
                    Key=outputImage,
                    Body=buffer,
                    ContentType='image/png',
                )
            except:
                app.logger.error("Failed to Upload Image")
                return "Failed to Upload Image"

            
        app.logger.info("Post Request Complete")
        return "Upload to S3 Complete"
        
