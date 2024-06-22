from flask_migrate import Migrate
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from flask_socketio import SocketIO
socketio = SocketIO()
# from flask_apscheduler import APScheduler 
# from apscheduler.schedulers.background import BackgroundScheduler
app = Flask(__name__)


app.config.from_object(Config)  
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# scheduler = APScheduler(scheduler=BackgroundScheduler())

login_manager = LoginManager()

login_manager.init_app(app)
socketio.init_app(app)
login_manager.login_view = 'login'

from app import views, models
