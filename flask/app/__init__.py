from flask import Flask
from logging.config import dictConfig
import os

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://flask.logging.wsgi_errors_stream'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': 'logging/app.log',
            'maxBytes': 1024
        }
    },
    'root': {
            'level': 'INFO',
            'handlers': ['wsgi', 'file']
    }
})

app = Flask(__name__)
 
from app import api
