import logging
from datetime import datetime

from flask import Blueprint, Response, jsonify
from flask_login import logout_user
from werkzeug.exceptions import HTTPException

from ..models import db, Libraries, Users
from ..utils.login_manager import current_user
from ..utils.rate_limiter import rate_limiter
from ..config import DATETIME_FORMAT


log = logging.getLogger(__name__)
api = Blueprint("api", __name__, url_prefix="/api")


@api.errorhandler(HTTPException)
def handle_exception(e: HTTPException):
    """
    Handle exceptions in API routes.
    """
    log.error(f"API Exception: {str(e)}", exc_info=e)
    return jsonify({
        "error": e.description,
        "code": e.code
    }), e.code

      
@api.route("/user", methods=["GET"])  
def get_current_user_info():
    """
    Get the information of the current user.
    """
    
    if not current_user.is_authenticated:
        return "Not logged in.", 401
    
    return jsonify({
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "library": current_user.current_library,
        "avatar_url": current_user.avatar_url,
        "locale": current_user.locale,
        "link_discord": current_user.discord_id is not None,
        "link_google": current_user.google_token is not None,
    })
    
    
@api.route("/user", methods=["DELETE"])
def delete_current_user():
    """
    Delete the current user's account.
    """
    
    if not current_user.is_authenticated:
        return "Not logged in.", 401
    
    user_id = current_user.id
    logout_user()
    
    user: Users = Users.query.filter_by(id=user_id).first()
    
    if not user:
        return "User not found.", 404
    
    db.session.delete(user)
    db.session.commit()
    
    if Users.query.filter_by(id=user_id).first() is not None:
        return "Failed to delete account.", 500
    
    return "Account deleted successfully.", 200
        
        
@api.route("/change_user_library/<string:library>", methods=["PUT"])
def change_user_library(library: str):
    """
    Change the library of the current user or anonymous.
    """
    if library is None:
        return "No library specified.", 400
    
    if not isinstance(library, str):
        return "Invalid library name.", 400
    
    if Libraries.query.filter_by(name=library) is None:
        return "Library not found.", 404
    
    if not current_user.is_authenticated:
        resp = Response("Library changed successfully.", 200)
        resp.set_cookie("current_library", library, max_age=60*60*24*30)
        return resp
    
    Users.query.filter_by(id=current_user.id).update({"current_library": library})
    db.session.commit()
    
    return "Library changed successfully.", 200


@api.route("/library/<string:library_name>", methods=["DELETE"])
def delete_library(library_name: str):
    """
    Delete a library.
    """
    if not current_user.is_authenticated:
        return "Not logged in.", 401
    
    library: Libraries = Libraries.query.filter_by(name=library_name).first()
    
    if not library:
        return "Library not found.", 404
    
    if library.author_id != current_user.id and not current_user.is_admin:
        return "Permission denied.", 403
    
    db.session.delete(library)
    db.session.commit()
    
    return "Library deleted successfully.", 200


@api.route("/favorites", methods=["GET"])
def get_user_favorites():
    """
    Get the current user's favorite library IDs.
    """
    
    if not current_user.is_authenticated:
        return "Not logged in.", 401
    
    favorite_ids = [lib.id for lib in current_user.favorite_libraries]
    return jsonify({"favorite_ids": favorite_ids})


@api.route("/favorites/<string:library_name>", methods=["PUT"])
def toggle_favorite(library_name: str):
    """
    Toggle favorite status for a library.
    """
    
    if not current_user.is_authenticated:
        return "Not logged in.", 401
    
    library: Libraries = Libraries.query.filter_by(name=library_name).first()
    
    if not library:
        return "Library not found.", 404
    
    if current_user in library.favorite_users:
        library.favorite_users.remove(current_user)
        msg = "Removed from favorites."
    
    else:
        library.favorite_users.append(current_user)
        msg = "Added to favorites."
    
    db.session.commit()
    
    return msg, 200


@api.route("/admin/rate_limit_stats", methods=["GET"])
def get_rate_limit_stats():
    """
    Get rate limiting statistics (admin only).
    """
    
    if not current_user.is_authenticated or not current_user.is_admin:
        return "Permission denied.", 403
    
    current_ip_stats = rate_limiter.get_ip_stats()
    
    banned_ips = []
    for ip, ban_time in rate_limiter.banned_ips.items():
        ban_end = datetime.fromtimestamp(ban_time)
        banned_ips.append({
            "ip": ip,
            "ban_until": ban_end.strftime(DATETIME_FORMAT)
        })
    
    return jsonify({
        "current_ip_stats": current_ip_stats,
        "banned_ips": banned_ips,
        "total_banned_ips": len(rate_limiter.banned_ips),
        "rate_limiting_enabled": rate_limiter.enabled
    })
