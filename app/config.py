import os
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env if it exists.

class Config(object):
    """Base Config Object"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'Som3$ec5etK*y')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'mysql://diabetes_user:Iamagirl2$@localhost/diabetes')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SCHEDULER_API_ENABLED = True
