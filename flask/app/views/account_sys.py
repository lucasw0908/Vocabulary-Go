import logging
from datetime import timedelta
from typing import Optional

from flask import Blueprint, abort, render_template, redirect, url_for, request, session, flash
from flask_login import login_user, logout_user, login_required
from flask_babel import _
from zenora import APIClient

from ..config import DISCORD_CLIENT_SECRET, DISCORD_TOKEN, DISCORD_OAUTH_URL, ADMINS
from ..models import db, Libraries, Users
from ..utils.forms import (
    LoginForm, RegisterForm, 
    AvatarUpdateForm, UsernameUpdateForm, BioUpdateForm, PasswordChangeForm, 
    PasswordResetRequestForm, ForgotPasswordForm
)
from ..utils.oauth import FlaskOAuth, google_flow
from ..utils.login_manager import current_user
from ..utils.secret import JWTManager
from ..utils.smtp import send_email
from ..utils.checker import email_checker


log = logging.getLogger(__name__)
account_sys = Blueprint("account_sys", __name__)
discord_client = APIClient(DISCORD_TOKEN, client_secret=DISCORD_CLIENT_SECRET, validate_token=False)


@account_sys.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        confirm = form.confirm.data
        
        if password != confirm:
            log.warning("Password confirmation does not match")
            flash(_("Passwords do not match"), "error")
            return render_template("account_sys/register.html", form=form)
        
        try:
            email_checker(email)
            
        except Exception as e:
            log.warning(f"Invalid email format: {email}, error: {e}")
            flash(_("Invalid email format"), "error")
            return render_template("account_sys/register.html", form=form)
        
        if Users.query.filter_by(email=email).first():
            log.warning(f"Email {email} is already registered")
            flash(_("Email already registered"), "error")
            return render_template("account_sys/register.html", form=form)
        
        new_user = Users(
            username=username,
            password=password,
            email=email,
            is_admin=False,
            unlimited_access=False,
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Send verification email
        lifetime = timedelta(hours=24)
        token = JWTManager.generate_jwt({"email": email}, lifetime=lifetime)
        verify_link = url_for("account_sys.verify_email", token_value=token, _external=True)
        send_email(
            to_address=email,
            subject=_("Email Verification"),
            body=render_template("smtp/verify_email.html", verify_link=verify_link, expire_in=int(lifetime.total_seconds() // 60)),
            subtype="html",
        )
        
        log.debug(f"User {email} registered successfully; verification email sent")
        flash(_("Registration successful. Please log in and check the verification mail in your email."), "success")
        return redirect("/login")
    
    return render_template("account_sys/register.html", form=form)


@account_sys.route("/login", methods=["GET", "POST"])
def login():
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user: Users = Users.query.filter_by(email=email).first()
        
        if user is None:
            log.warning(f"Login attempt with unregistered email: {email}")
            flash(_("Invalid email or password"), "error")
            return render_template("account_sys/login.html", form=form)
        
        if user.password is None:
            log.warning(f"Login attempt for OAuth-only account: {email}")
            flash(_("This account uses OAuth for login. Please use the OAuth login method."), "error")
            return render_template("account_sys/login.html", form=form)
        
        if user.check_password(password):
            login_user(user, remember=form.remember.data)
            log.debug(f"User {email} logged in successfully, remember={form.remember.data}")
            resp = redirect("/")
            resp.delete_cookie("current_library")
            return resp
        
        else:
            log.warning(f"Failed login attempt for user {email}")
            flash(_("Invalid email or password"), "error")
            return render_template("account_sys/login.html", form=form)
            
    return render_template("account_sys/login.html", form=form)


@account_sys.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    
    def render(error: Optional[str] = None):
        if error is not None:
            log.warning(f"Forgot password error: {error}")
            
        return render_template("account_sys/forgot_password.html", form=form, error=error)
    
    if form.validate_on_submit():
        email = form.email.data
        
        if Users.query.filter_by(email=email).first() is None:
            return render(_("No account associated with this email."))
        
        lifetime = timedelta(hours=1)
        token = JWTManager.generate_jwt({"email": email}, lifetime=lifetime)
        reset_link = url_for("account_sys.reset_password", token_value=token, _external=True)
        
        send_email(
            to_address=email,
            subject=_("Password Reset Request"),
            body=render_template("smtp/reset_password.html", reset_link=reset_link, expires_in=int(lifetime.total_seconds() // 60)),
            subtype="html",
        )
        flash(_("Password reset link sent. Please check your email."), "success")
        return redirect("/login")
    
    return render()


@account_sys.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    resp = redirect("/login")
    resp.set_cookie("s-correctCount", "", expires=0)
    resp.set_cookie("s-wrongCount", "", expires=0)
    resp.set_cookie("s-usedIndices", "", expires=0)
    resp.set_cookie("correctCount", "", expires=0)
    resp.set_cookie("wrongCount", "", expires=0)
    resp.set_cookie("usedIndices", "", expires=0)
    return resp


@account_sys.route("/oauth/discord", methods=["GET"])
def discord_oauth():
    
    if current_user.is_authenticated and current_user.discord_id is not None:
        log.warning(f"User {current_user.email} attempted to re-link Discord account")
        flash(_("Discord account already linked."), "warning")
        return redirect(url_for("account_sys.settings"))
    
    if current_user.is_authenticated and current_user.password is None:
        log.warning(f"User {current_user.email} attempted to link Discord without a password set")
        flash(_("Set a password before linking Discord."), "warning")
        return redirect(url_for("account_sys.settings"))
    
    return redirect(DISCORD_OAUTH_URL)


@account_sys.route("/oauth/google", methods=["GET"])
def google_oauth():
    
    if current_user.is_authenticated and current_user.google_id is not None:
        log.warning(f"User {current_user.email} attempted to re-link Google account")
        flash(_("Google account already linked."), "warning")
        return redirect(url_for("account_sys.settings"))
    
    if current_user.is_authenticated and current_user.password is None:
        log.warning(f"User {current_user.email} attempted to link Google without a password set")
        flash(_("Set a password before linking Google."), "warning")
        return redirect(url_for("account_sys.settings"))

    auth_url, state = google_flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )
    session["google_oauth_state"] = state
    return redirect(auth_url)


@account_sys.route("/oauth/callback", methods=["GET"])
def callback():
    try:
        if ("state" in request.args) and (request.args["state"] == session.get("google_oauth_state")):
            id_info, google_token = FlaskOAuth.google()
            session.pop("google_oauth_state", None)

        elif "code" in request.args:
            discord_current_user, discord_token = FlaskOAuth.discord()
        
        else:
            log.warning("No valid OAuth parameters found in callback")
            return abort(400, description=_("Invalid OAuth callback parameters."))
        
    except FlaskOAuth.OAuthError as e:
        if isinstance(e, FlaskOAuth.GoogleOAuthError):
            log.warning(f"Google OAuth error: {e}")
            
        elif isinstance(e, FlaskOAuth.DiscordOAuthError):
            log.warning(f"Discord OAuth error: {e}")
            
        return abort(400, description=_("OAuth authentication failed."))
            
    user: Optional[Users] = current_user if current_user.is_authenticated else Users(
        username=None, password=None, email=None, is_admin=False
    )
            
    if "id_info" in locals() and "google_token" in locals():
        # Try to find existing user by Google ID or email
        user = Users.query.filter(
            (Users.google_id == id_info["sub"]) |
            (Users.email == id_info.get("email", None))
        ).first() or user
        user.google_id = id_info["sub"]
        user.google_token = google_token
        user.email_verified = id_info.get("email_verified", False) or user.email_verified
        user.username = user.username or id_info.get("name", user.username)
        user.email = user.email or id_info.get("email", user.email)
        user.avatar_url = user.avatar_url or id_info.get("picture", user.avatar_url)
        user.locale = user.locale or id_info.get("locale", user.locale)
        user.is_admin = user.is_admin or (user.email in ADMINS)

    elif "discord_current_user" in locals() and "discord_token" in locals():
        # Try to find existing user by Discord ID or email
        user = Users.query.filter(
            (Users.discord_id == str(discord_current_user.id)) |
            (Users.email == discord_current_user.email)
        ).first() or user
        user.discord_id = str(discord_current_user.id)
        user.discord_token = discord_token
        user.username = user.username or discord_current_user.username
        # Alternatively, you could use the discriminator to ensure uniqueness (Gmail is ascii only)
        # user.username = user.username or f"{discord_current_user.username}#{discord_current_user.discriminator}"
        user.email = user.email or discord_current_user.email
        user.avatar_url = user.avatar_url or discord_current_user.avatar_url
        user.locale = user.locale or discord_current_user.locale
        user.is_admin = user.is_admin or (discord_current_user.username in ADMINS)

    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    log.debug(f"User {user.email} logged in via OAuth successfully")
    
    if user.password is not None:
        return redirect("/settings")
    
    return redirect("/")


@account_sys.route("/oauth/discord/unlink", methods=["GET"])
@login_required
def discord_unlink():
    
    if current_user.password is None:
        log.warning(f"User {current_user.email} attempted to unlink Discord but has no password set")
        return redirect(url_for("account_sys.settings", error=_("Set a password before unlinking Discord.")))
    
    if current_user.discord_id is None:
        log.warning(f"User {current_user.email} attempted to unlink Discord but no Discord account is linked")
        return abort(400, description=_("No Discord account linked."))
    
    current_user.discord_id = None
    current_user.discord_token = None
    db.session.commit()
    log.debug(f"User {current_user.email} unlinked Discord account successfully")
    return redirect("/settings")


@account_sys.route("/oauth/google/unlink", methods=["GET"])
@login_required
def google_unlink():
    
    if current_user.password is None:
        log.warning(f"User {current_user.email} attempted to unlink Google but has no password set")
        return redirect(url_for("account_sys.settings", error=_("Set a password before unlinking Google.")))
    
    if current_user.google_id is None:
        log.warning(f"User {current_user.email} attempted to unlink Google but no Google account is linked")
        return abort(400, description=_("No Google account linked."))
    
    current_user.google_id = None
    current_user.google_token = None
    db.session.commit()
    log.debug(f"User {current_user.email} unlinked Google account successfully")
    return redirect("/settings")


@account_sys.route("/profile/<int:user_id>", methods=["GET"])
def profile(user_id: int):
    
    user: Users = Users.query.filter_by(id=user_id).first()
    
    if user is None:
        abort(404)
    
    libraries = Libraries.query.filter_by(author_id=user.id, public=True).all()
    
    user_info = {
        "username": user.username,
        "avatar_url": user.avatar_url,
        "libraries": libraries,
        "created_at": user.created_at,
        "bio": user.bio,
    }
    
    return render_template("account_sys/profile.html", user=user_info, current_user=current_user)


@account_sys.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    
    avatar_form, username_form, bio_form, password_form = \
        AvatarUpdateForm(), UsernameUpdateForm(), BioUpdateForm(), PasswordChangeForm()
        
    forms: dict[str, AvatarUpdateForm | UsernameUpdateForm | BioUpdateForm | PasswordChangeForm] = \
        {"avatar": avatar_form, "bio": bio_form, "password": password_form}

    if request.method == "GET":
        username_form.username.data = current_user.username
        bio_form.bio.data = current_user.bio

    def render(error: Optional[str] = None):
        if error:
            log.warning(f"Settings update error for user {current_user.username}: {error}")
            
        return render_template(
            "account_sys/settings.html",
            current_user=current_user,
            avatar_form=avatar_form,
            bio_form=bio_form,
            password_form=password_form,
            error=error,
        )

    if request.method == "POST":
        submit_type = request.form.get("submit")
        form = forms.get(submit_type)

        if form is None:
            return render(_("Unknown settings submission type: %(submit_type)s", submit_type=submit_type))

        if not form.validate_on_submit(): 
            return render(_("Form validation failed for %(submit_type)s", submit_type=submit_type))

        if submit_type == "avatar":
            current_user.set_avatar(form.avatar.data)
            
        elif submit_type == "username":        
            current_user.username = form.username.data.strip()
            
        elif submit_type == "bio":
            current_user.bio = form.bio.data.strip()
            
        elif submit_type == "password":
            if current_user.password is not None:
                if not form.current_password.data:
                    return render(_("Please enter your current password."))
                
                if not current_user.check_password(form.current_password.data.strip()):
                    return render(_("Current password is incorrect."))
            
            if form.new_password.data.strip() != form.confirm_password.data.strip():
                return render(_("New password and confirmation do not match."))
            
            current_user.set_password(form.new_password.data.strip())

        log.debug(f"{submit_type.capitalize()} updated for user {current_user.username}")
        db.session.commit()

    return render()


@account_sys.route("/reset_password/<string:token_value>", methods=["GET", "POST"])
def reset_password(token_value: str):
    
    token_value = token_value.strip()
    payload = JWTManager.validate_jwt(token_value)
    
    if payload is None or "email" not in payload:
        log.warning(f"Invalid or expired password reset token")
        return abort(400, description="Invalid or expired token.")
    
    email = payload["email"]
    
    form = PasswordResetRequestForm()
    
    if request.method == "POST" and form.validate_on_submit():
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data
        
        if new_password != confirm_password:
            log.warning("New password confirmation does not match")
            flash(_("Passwords do not match"), "error")
            return render_template("account_sys/reset_password.html", form=form, email=email)
        
        user: Users = Users.query.filter_by(email=email).first()
        
        if user is None:
            log.error(f"No user found with email {email} during password reset")
            return abort(400, description=_("User not found."))
        
        user.set_password(new_password)
        db.session.commit()
        
        log.debug(f"Password reset successfully for user {email}")
        return redirect("/login")
    
    return render_template("account_sys/reset_password.html", form=form, email=email)
    
    
@account_sys.route("/verify_email/<string:token_value>")
def verify_email(token_value: str):
    
    token_value = token_value.strip()
    payload = JWTManager.validate_jwt(token_value)
    
    if payload is None or "email" not in payload:
        log.warning("Invalid or expired email verification token")
        return abort(400, description="Invalid or expired token.")
    
    email = payload["email"]
    
    user: Users = Users.query.filter_by(email=email).first()
    
    if user is None:
        log.error(f"No user found with email {email} during email verification")
        return abort(400, description=_("User not found."))
    
    user.email_verified = True
    db.session.commit()
    
    log.debug(f"Email {email} verified successfully")
    flash(_("Email verified successfully."), "success")
    return redirect(url_for("main.index"))
