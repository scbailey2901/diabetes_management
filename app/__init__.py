from flask_migrate import Migrate
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .config import Config
# from flask_socketio import SocketIO
# socketio = SocketIO()
# from flask_oauthlib.client import OAuth
app = Flask(__name__)


app.config.from_object(Config)  
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# scheduler = APScheduler(scheduler=BackgroundScheduler())

login_manager = LoginManager(app)

# login_manager.init_app(app)
# socketio.init_app(app)
login_manager.login_view = 'login'
# oauth = OAuth(app)

# wearable = oauth.remote_app(
#     'wearable',
#     consumer_key=app.config['WEARABLE_CLIENT_ID'],
#     consumer_secret=app.config['WEARABLE_CLIENT_SECRET'],
#     request_token_params={'scope': 'read'},
#     base_url='https://api.wearable.com/',
#     request_token_url=None,
#     access_token_method='POST',
#     access_token_url='https://api.wearable.com/oauth2/token',
#     authorize_url='https://api.wearable.com/oauth2/authorize'
# )

from app import views, models
