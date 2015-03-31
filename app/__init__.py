from flask.ext.login import LoginManager
from flask.ext.bootstrap import Bootstrap
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from config import config
from flask import Flask

bootstrap = Bootstrap()
manager = Manager()
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
moment = Moment()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    login_manager.init_app(app)
    
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    return app
