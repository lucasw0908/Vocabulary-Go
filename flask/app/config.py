import os
import json
from datetime import timedelta

from dotenv import load_dotenv


# Generate a random secret key
SECRET_KEY = os.urandom(12).hex()


# Application base directory
BASEDIR = os.path.abspath(os.path.dirname(__file__))
SETTINGS_PATH = os.path.join(BASEDIR, "settings.json")


# Load settings from JSON file
if not os.path.exists(SETTINGS_PATH):
    raise FileNotFoundError("The settings.json file is missing. Please ensure it exists in the app directory.")

with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

try: 
    # Server Settings
    SERVER_HOST = SETTINGS["server"]["host"]
    SERVER_PORT = SETTINGS["server"]["port"]
    DEBUG_MODE = SETTINGS["server"]["debug"]

    # Database Settings
    DATABASE_SQLITE = SETTINGS["database"]["sqlite"]
    DATABASE_ECHO = SETTINGS["database"]["echo"]
    DATABASE_POOL_SIZE = SETTINGS["database"]["pool_size"]
    DATABASE_POOL_RECYCLE = SETTINGS["database"]["pool_recycle"]

    # Security Settings
    CSRF_PROTECTION = SETTINGS["security"]["csrf_protection"]
    PASSWORD_HASHING_ALGORITHM = SETTINGS["security"]["password_hashing_algorithm"]
    PASSWORD_HASHING_ROUNDS = SETTINGS["security"]["password_hashing_rounds"]
    RATE_LIMITING = SETTINGS["security"]["rate_limiting"]

    # Logging Settings
    LOG_LEVEL = SETTINGS["logging"]["level"]
    LOG_FORMAT = SETTINGS["logging"]["format"]
    LOG_FILE = SETTINGS["logging"]["file"]
    LOG_MAX_BYTES = SETTINGS["logging"]["max_bytes"]
    LOG_BACKUP_COUNT = SETTINGS["logging"]["backup_count"]

    # API Settings
    API_MODEL_TYPE = SETTINGS["api"]["model_type"] # "groq" or "gemini"
    API_MODEL_NAME = SETTINGS["api"]["model_name"]
    API_RETRY_ATTEMPTS = SETTINGS["api"]["retry_attempts"]
    API_RETRY_DELAY = SETTINGS["api"]["retry_delay"]
    API_GENERATION_DURATION = SETTINGS["api"]["generation_duration"]
    MAX_SENTENCES_PER_WORD = SETTINGS["api"]["max_sentences_per_word"]

    # SMTP Settings
    SMTP_SERVER = SETTINGS["smtp"]["server"]
    SMTP_PORT = SETTINGS["smtp"]["port"]
    DEFAULT_SENDER = SETTINGS["smtp"]["default_sender"]

    # Development Settings
    ADMINS = SETTINGS["development"]["admins"]
    ALWAYS_UPDATE_DIST = SETTINGS["development"]["always_update_dist"]
    INIT_GENERATOR = SETTINGS["development"]["init_generator"]

    # Defaults
    SUPPORTED_LANGUAGES = SETTINGS["defaults"]["supported_languages"]
    DEFAULT_THEME = SETTINGS["defaults"]["theme"] # It is useless now
    DEFAULT_ITEMS_PER_PAGE = SETTINGS["defaults"]["items_per_page"]
    MAX_CONTENT_LENGTH = SETTINGS["defaults"]["max_content_length"]
    MAX_AVATAR_SIZE = SETTINGS["defaults"]["max_avatar_size"]
    DATETIME_FORMAT = SETTINGS["defaults"]["datetime_format"]
    DEFAULT_LIBRARY = SETTINGS["defaults"]["library"]
    DEFAULT_LOCALE = SETTINGS["defaults"]["locale"]
    DEFAULT_AVATAR = SETTINGS["defaults"]["avatar"]
    DEFAULT_AVATAR_FOLDER = SETTINGS["defaults"]["avatar_folder"]

    # Social Links
    GITHUB_LINK = SETTINGS["social_links"]["github"]
    DISCORD_LINK = SETTINGS["social_links"]["discord"]
    TWITTER_LINK = SETTINGS["social_links"]["twitter"]
    FACEBOOK_LINK = SETTINGS["social_links"]["facebook"]
    INSTAGRAM_LINK = SETTINGS["social_links"]["instagram"]

    # Fallback Quotes
    FALLBACK_QUOTES = SETTINGS["fallbackQuotes"]
    
except KeyError as e:
    raise KeyError(f"Missing configuration key: {e}. Please check your settings.json file.")

try:
    with open(os.path.join(os.path.dirname(__file__), 'local_settings.py')) as f:
        exec(f.read(), globals())
except IOError:
    pass


# Load environment variables from .env file
load_dotenv(os.path.join(BASEDIR, ".env"), override=True)

SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
SQLITE_DATABASE_URI = "sqlite:///" + os.path.join(BASEDIR, DATABASE_SQLITE)

# OAuth and API configuration
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Discord OAuth configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_OAUTH_URL = f"https://discord.com/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify+email" 

# Google OAuth configuration
GOOGLE_SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [REDIRECT_URI],
        "scopes": GOOGLE_SCOPES,
        "project_id": "Vocabulary Website Project",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    }
}

# API keys
APIKEYS = [key.strip() for key in os.getenv("APIKEYS").split(",")]

# SMTP configuration
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# System user configuration
SYSTEM_USERNAME = os.getenv("SYSTEM_USERNAME")
SYSTEM_EMAIL = os.getenv("SYSTEM_EMAIL")
SYSTEM_PASSWORD = os.getenv("SYSTEM_PASSWORD")  

if not all([
    SQLALCHEMY_DATABASE_URI,
    REDIRECT_URI,
    DISCORD_TOKEN,
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    APIKEYS,
    SMTP_USER,
    SMTP_PASSWORD,
    SYSTEM_USERNAME,
    SYSTEM_EMAIL,
    SYSTEM_PASSWORD
]):
    raise ValueError("Environment variables are not fully set. Please check your .env file.")


class Config(object):
    JSON_AS_ASCII = False
    SECRET_KEY = SECRET_KEY
    
    # Database Settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "echo": DATABASE_ECHO,
        "pool_size": DATABASE_POOL_SIZE,
        "pool_recycle": DATABASE_POOL_RECYCLE,
    }
    
    # Session Settings
    SESSION_TYPE = "sqlalchemy"
    SESSION_KEY_PREFIX = "session:"
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    
    # Cookie Settings
    REMEMBER_COOKIE_DURATION = timedelta(days=31)
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    
    # Babel Settings
    BABEL_DEFAULT_LOCALE = DEFAULT_LOCALE
    BABEL_TRANSLATION_DIRECTORIES = os.path.join(BASEDIR, "translations")


class ProdConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI or SQLITE_DATABASE_URI
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = SQLITE_DATABASE_URI
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
