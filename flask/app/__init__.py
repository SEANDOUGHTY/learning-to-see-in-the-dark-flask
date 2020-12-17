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
    },
    'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
    }
})

app = Flask(__name__)
 
from app import api
