from flask_migrate import Migrate
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .config import Config
app = Flask(__name__)

db = SQLAlchemy(app)
app.config.from_object(Config)
migrate = Migrate(app, db)
# Flask-Login login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from app import views, models
