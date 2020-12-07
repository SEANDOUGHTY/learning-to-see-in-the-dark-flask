from app import app
import cv2
import math
import numpy as np
from PIL import Image

def importImage(im, ratio):
    app.logger.debug("Converting image to Numpy Array")
    im = np.asarray(Image.open(im))
            
    app.logger.debug("Scaling and removing black levels")
    im = np.maximum(im - 0.0, 0) / (255.0 - 0.0)  # subtract the black level

    app.logger.debug("Cast to Float32")
    im = im.astype(np.float32)

    im *= ratio    
    return im

def inferTransform(im):
    # scaling image down to a max dimension of 512, maintaining aspect ratio
    app.logger.info("Imported image is: %d X %d" % (im.shape[0], im.shape[1]))
    if max(im.shape) > 512:
        scale_factor = 512 / max(im.shape)
        H = int(im.shape[0] * scale_factor)
        W = int(im.shape[1] * scale_factor)
        app.logger.info("Rescaling image to: %d X %d" % (H, W))
        im = cv2.resize(im, (W,H), cv2.INTER_AREA)

    # cropping image to nearest 16, to allow torch to compute
    app.logger.debug("Trimming image to size")
    H = math.floor(im.shape[0]/16.0)*16
    W = math.floor(im.shape[1]/16.0)*16
    im = im[:H, :W, :]

    return im