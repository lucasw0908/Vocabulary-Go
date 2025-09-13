from flask_login import AnonymousUserMixin, LoginManager, current_user as flask_current_user
from flask import redirect, request

from ..models import Users, Libraries
from ..config import DEFAULT_LIBRARY


class Anonymous(AnonymousUserMixin):
    
    username: str = "Anonymous"
    password: str = ""
    email: str = ""
    is_admin: bool = False
    bio: str = ""

    created_at = ...
    updated_at = ...

    locale = ...
    avatar_url = ...
    logins = ...

    _current_library = DEFAULT_LIBRARY
    libraries = ...
    favorite_libraries = ...

    # Discord fields
    discord_token = ...
    discord_id = ...

    # Google fields
    google_token = ...
    google_id = ...
    
    @property
    def current_library(self):
        
        if (cookie_current_library := request.cookies.get("current_library")) is not None:
            self._current_library = cookie_current_library
            
        if Libraries.query.filter_by(name=self._current_library).first() is not None:
            return self._current_library
            
        return DEFAULT_LIBRARY
    
    def __repr__(self):
        return "<Anonymous User>"
    

login_manager = LoginManager()
login_manager.login_view = "account_sys.login"
login_manager.session_protection = "strong"
login_manager.anonymous_user = Anonymous

current_user: Anonymous | Users = flask_current_user


@login_manager.user_loader
def load_user(user_id):
    """
    Load user by ID.
    
    Parameters
    ----------
    user_id : str
        The ID of the user to load.
    
    Returns
    -------
    Users
        The user object if found, otherwise None.
    """
    return Users.query.get(int(user_id))


@login_manager.unauthorized_handler
def handle_unauthorized():
    return redirect("/login")
