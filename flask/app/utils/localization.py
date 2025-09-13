from flask import request, session, g
from flask_babel import Babel

from ..utils.login_manager import current_user
from ..config import SUPPORTED_LANGUAGES


def select_locale():
    
    if g.get("locale") is not None:
        return g.locale
    
    if "lang" in session and session["lang"] in SUPPORTED_LANGUAGES:
        return session["lang"]
    
    if current_user.is_authenticated and getattr(current_user, "locale", None) in SUPPORTED_LANGUAGES:    
        return current_user.locale
    
    return request.accept_languages.best_match(SUPPORTED_LANGUAGES)


babel = Babel()
