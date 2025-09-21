import logging
import logging.handlers
import os
import sys

from flask import Flask
from flask_session import Session
from flask_wtf import CSRFProtect

from .config import (
    ProdConfig, DevConfig,
    BASEDIR, 
    DEBUG_MODE,
    LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT,
    CSRF_PROTECTION,
    DATETIME_FORMAT,
    INIT_GENERATOR,
)
from .models import db, migrate
from .generator import init_generator
from .utils.admin import init_admin
from .utils.secret import bcrypt
from .utils.initialize import init_models
from .utils.localization import babel, select_locale
from .utils.login_manager import login_manager
from .utils.rate_limiter import rate_limit_middleware


IS_MIGRATING = "db" in sys.argv and any(cmd in sys.argv for cmd in ["upgrade", "downgrade", "migrate"])

log = logging.getLogger(__name__)


def init_logger() -> None:
    """
    Parameters
    ----------
    debug: :type:`bool`
        If debug is true, the logger will log all messages.
    """
        
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATETIME_FORMAT, style="{")
    
    log.setLevel(LOG_LEVEL)
        
    if os.access(BASEDIR, os.W_OK):
        LOGDIR = os.path.join(BASEDIR, "logs")
        
        if not os.path.exists(LOGDIR):
            os.makedirs(LOGDIR)
            
        log.debug(f"Log directory: {LOGDIR}")
            
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(LOGDIR, LOG_FILE),
            encoding="utf-8",
            maxBytes=LOG_MAX_BYTES, 
            backupCount=LOG_BACKUP_COUNT
        )
        
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    
    log.info("Logger initialized")
    
    
def app_load_blueprints(app: Flask) -> None:
    """
    Load all blueprints
    
    Parameters
    ----------
    app: :class:`Flask`
        The flask app.
    """
    
    from .views.api import api
    from .views.account_sys import account_sys
    from .views.error_handler import error_handler
    from .views.main import main
    from .views.mail import mail
    
    app.register_blueprint(api)
    app.register_blueprint(account_sys)
    app.register_blueprint(error_handler)
    app.register_blueprint(main)
    app.register_blueprint(mail)
    
    log.info("Blueprints loaded")
    
    
def init_db(app: Flask) -> None:
    """
    Init the database.
    
    Parameters
    ----------
    app: :class:`Flask`
        The flask app.
    """
    
    __import__("app.models.users")
    __import__("app.models.words")
    __import__("app.models.libraries")
    __import__("app.models.sentences")
    
    db.init_app(app)
        
    log.info("Database initialized")
    

def create_app(config=None) -> Flask:
    """
    Returns
    -------
    app: :class:`Flask`
        A flask app.
    """
    # Initialize the logger
    init_logger()
    
    # Initialize the app
    app = Flask(__name__)
    app.config.from_object(config or (DevConfig if DEBUG_MODE else ProdConfig))
    
    # Initialize the bcrypt
    bcrypt.init_app(app)
    
    # Initialize the database
    init_db(app)
    
    # Initialize the migrations
    migrate.init_app(app, db)
    
    # Initialize the sqlalchemy session
    app.config["SESSION_SQLALCHEMY"] = db
    Session(app)
    log.info("Using SQLAlchemy for session storage")
    
    # Initialize the login manager
    login_manager.init_app(app)
    
    # Initialize the localization
    babel.init_app(app, locale_selector=select_locale)
    
    # Initialize the admin interface
    init_admin(app)
    
    # Initialize the CSRF protection
    if CSRF_PROTECTION:
        csrf = CSRFProtect(app)
        csrf.init_app(app)
        csrf.exempt("/api/*")  # Exempt API endpoints from CSRF
        log.info("CSRF protection is enabled")
    
    # Load the blueprints
    app_load_blueprints(app)

    # Initialize rate limiting middleware
    @app.before_request
    def before_request():
        """Rate limiting middleware"""
        response = rate_limit_middleware()
        if response:
            return response
    
    with app.app_context(): 

        # Initialize the models
        if not IS_MIGRATING:
            init_models()
    
            # Initialize the questions generator
            if INIT_GENERATOR:
                init_generator()
    
    log.info("App initialized")

    return app
