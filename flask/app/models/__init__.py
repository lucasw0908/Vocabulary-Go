# ruff: noqa: E402
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy(session_options={"autoflush": False})
migrate = Migrate()

from .users import Users
from .words import Words
from .sentences import Sentences
from .libraries import Libraries

__all__ = ["db", "migrate", "Users", "Words", "Sentences", "Libraries"]