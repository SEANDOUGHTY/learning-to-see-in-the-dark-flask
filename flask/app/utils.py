import cv2
import math
import numpy as np

def inferTransform(im):
    # scaling image down to a max dimension of 512, maintaining aspect ratio
    if max(im.shape) > 512:
        scale_factor = 512 / max(im.shape)
        H = int(im.shape[0] * scale_factor)
        W = int(im.shape[1] * scale_factor)
        im = cv2.resize(im, (W,H), cv2.INTER_AREA)


    # cropping image to nearest 16, to allow torch to compute
    H = math.floor(im.shape[0]/16.0)*16
    W = math.floor(im.shape[1]/16.0)*16
    im = im[:H, :W, :]

    return im