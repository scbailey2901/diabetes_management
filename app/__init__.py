from flask import Flask
from .config import Config
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = '4b5fb3a442cb0ba9ee3312fb9126bec627d32ce4d882f8d02ebb1642a902fb23'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://diabetes_user:Iamagirl2$@localhost/diabetes'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

from app import models 
from app import views

