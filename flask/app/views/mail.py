import logging
from datetime import timedelta

from flask import Blueprint, url_for, render_template
from flask_babel import _

from ..models import Users
from ..utils.rate_limiter import RateLimiter, rate_limit_middleware
from ..utils.smtp import send_email
from ..utils.secret import TokenManager


log = logging.getLogger(__name__)
mail = Blueprint("mail", __name__, url_prefix="/mail")
rate_limiter = RateLimiter(
    requests_per_minute=1,
    requests_per_hour=5,
    requests_per_day=10,
)


@mail.before_request
def before_request():
    """Rate limiting middleware"""
    response = rate_limit_middleware(rate_limiter)
    if response:
        return response


@mail.route("/reset_password/<string:email>", methods=["POST"])
def reset_password(email: str):
    """
    Send a password reset email to the specified address.
    """
    
    if Users.query.filter_by(email=email).first() is None:
        return _("Email not found."), 404
    
    for available_token in TokenManager.available_tokens:
        if TokenManager.get_data_from_token(available_token.value) == email:
            TokenManager.available_tokens.remove(available_token)
    
    token = TokenManager.generate_token(email)
    reset_link = url_for("account_sys.reset_password", token_value=token.value.decode("utf-8"), _external=True)
    
    send_email(
        to_address=email,
        subject=_("Password Reset Request"),
        body=render_template("smtp/reset_password.html", reset_link=reset_link, expires_in=int(token.lifetime.total_seconds() // 60)),
        subtype="html",
    )
    
    log.debug(f"Sent password reset email to {email} with token {token}.")
    
    return _("Password reset email sent."), 200


@mail.route("/verify_email/<string:email>", methods=["POST"])
def verify_email(email: str):
    """
    Send an email verification email to the specified address.
    """
    
    user: Users = Users.query.filter_by(email=email).first()
    
    if user is None:
        return _("Email not found."), 404
    
    if user.email_verified:
        return _("Email already verified."), 400
    
    for available_token in TokenManager.available_tokens:
        if TokenManager.get_data_from_token(available_token.value) == email:
            TokenManager.available_tokens.remove(available_token)
    
    token = TokenManager.generate_token(email, lifetime=timedelta(minutes=30))
    verify_link = url_for("account_sys.verify_email", token_value=token.value.decode("utf-8"), _external=True)
    
    send_email(
        to_address=email,
        subject=_("Email Verification"),
        body=render_template("smtp/verify_email.html", verify_link=verify_link, expire_in=int(token.lifetime.total_seconds() // 60)),
        subtype="html",
    )
    
    log.debug(f"Sent email verification to {email} with token {token}.")
    
    return _("Email verification sent."), 200
