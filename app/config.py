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
    CLIENT_ID = os.environ.get("CLIENT_ID",'23PF67')
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET",'8731265148303be966f71bd191df1af4')
    REDIRECT_URI = os.environ.get("REDIRECT_URI",'http://localhost:8080/callback')
    # SCHEDULER_API_ENABLED = True
