from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import BooleanField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, Optional

from ..config import MAX_AVATAR_SIZE


class LoginForm(FlaskForm):
    email = StringField(_l("Email"), validators=[
        DataRequired(),
        Length(max=60, message=_l("Email is too long (max %(limit)s characters)", limit=60))
    ])
    password = PasswordField(_l("Password"), validators=[
        DataRequired(),
        Length(min=6, message=_l("Password is too short (min %(limit)s characters)", limit=6)),
        Length(max=20, message=_l("Password is too long (max %(limit)s characters)", limit=20))
    ])
    remember = BooleanField(_l("Remember Me"), default=True)
    submit = SubmitField(_l("Login"))


class RegisterForm(FlaskForm):
    username = StringField(_l("Username"), validators=[
        DataRequired(), 
        Length(max=30, message=_l("Username is too long (max %(limit)s characters)", limit=30))
    ])
    email = StringField(_l("Email"), validators=[
        DataRequired(),
        Length(max=60, message=_l("Email is too long (max %(limit)s characters)", limit=60))
    ])
    password = PasswordField(_l("Password"), validators=[
        DataRequired(),
        Length(min=6, message=_l("Password is too short (min %(limit)s characters)", limit=6)),
        Length(max=20, message=_l("Password is too long (max %(limit)s characters)", limit=20))
    ])
    confirm = PasswordField(_l("Confirm Password"), validators=[
        DataRequired(), EqualTo("password", message=_l("Passwords must match"))
    ])
    submit = SubmitField(_l("Register"))


class AvatarUpdateForm(FlaskForm):
    avatar = FileField(_l("Avatar"), validators=[
        FileRequired(),
        FileAllowed(["jpg", "jpeg", "png"], _l("Images only!")),
        Length(max=MAX_AVATAR_SIZE, message=_l("Avatar file is too large (max %(limit)s MB)", limit=MAX_AVATAR_SIZE // (1024 * 1024)))
    ])
    submit = SubmitField(_l("Update Avatar"))
    
    
class UsernameUpdateForm(FlaskForm):
    username = StringField(_l("Username"), validators=[
        DataRequired(),
        Length(min=3, message=_l("Username is too short (min %(limit)s characters)", limit=3)),
        Length(max=30, message=_l("Username is too long (max %(limit)s characters)", limit=30))
    ])
    submit = SubmitField(_l("Update Username"))


class BioUpdateForm(FlaskForm):
    bio = TextAreaField(_l("Bio"), validators=[
        Optional(),
        Length(max=75, message=_l("Bio is too long (max %(limit)s characters)", limit=75))
    ])
    submit = SubmitField(_l("Update Bio"))


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField(_l("Current Password"))
    new_password = PasswordField(_l("New Password"), validators=[
        DataRequired(),
        Length(min=6, message=_l("Password is too short (min %(limit)s characters)", limit=6)),
        Length(max=20, message=_l("Password is too long (max %(limit)s characters)", limit=20))
    ])
    confirm_password = PasswordField(_l("Confirm New Password"), validators=[
        DataRequired(), EqualTo("new_password", message=_l("Passwords must match"))
    ])
    submit = SubmitField(_l("Change Password"))
    
    
class PasswordResetRequestForm(FlaskForm):
    new_password = PasswordField(_l("New Password"), validators=[
        DataRequired(),
        Length(min=6, message=_l("Password is too short (min %(limit)s characters)", limit=6)),
        Length(max=20, message=_l("Password is too long (max %(limit)s characters)", limit=20))
    ])
    confirm_password = PasswordField(_l("Confirm New Password"), validators=[
        DataRequired(), EqualTo("new_password", message=_l("Passwords must match"))
    ])
    submit = SubmitField(_l("Request Password Reset"))


class ForgotPasswordForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired()])
    submit = SubmitField(_l("Send Reset Password Mail"))


class LibraryForm(FlaskForm):
    name = StringField(_l("Library Name"), validators=[
        DataRequired(),
        Length(max=50, message=_l("Library name is too long (max %(limit)s characters)", limit=50))
    ])
    description = TextAreaField(_l("Description"), validators=[
        Optional(),
        Length(max=200, message=_l("Description is too long (max %(limit)s characters)", limit=200))
    ])
    public = BooleanField(_l("Public Library"))
    words = TextAreaField(_l("Words (JSON format)"), validators=[
        DataRequired(),
        Length(max=10000, message=_l("Words JSON is too long (max %(limit)s characters)", limit=10000))
    ])
    submit = SubmitField(_l("Create Library"))
