import logging

from flask import Blueprint, render_template
from werkzeug.exceptions import HTTPException

from ..utils.login_manager import current_user


log = logging.getLogger(__name__)
error_handler = Blueprint("error_handler", __name__)


@error_handler.app_errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    """
    Handle HTTP exceptions by rendering a custom error page.
    
    Parameters
    ----------
    e : HTTPException
        The exception that was raised.
    
    Returns
    -------
    Response
        A Flask response object with the rendered error page and appropriate status code.
    """
    if e.code >= 500:
        log.error(f"HTTP Exception: {e.code} - {e.description}")
        
    return (
        render_template(
            "error.html",
            code=e.code,
            message=e.description,
            suppress_global_modal=True,
            user=current_user,
        ),
        e.code,
    )