from flask import Flask
from logging.config import dictConfig
import os
from flask_cors import CORS

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
CORS(app)
from app import api
