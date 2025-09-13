import io
import logging
import os
import requests
import hashlib
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from flask import url_for, request
from flask_login import UserMixin
from sqlalchemy import String, Boolean, DateTime, PickleType
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.datastructures import FileStorage

from . import db
from ..config import BASEDIR, DATETIME_FORMAT, DEFAULT_LOCALE, DEFAULT_AVATAR, DEFAULT_AVATAR_FOLDER
from ..utils.secret import hash_password, check_password
from ..utils.image_processing import process_image

if TYPE_CHECKING:
    from .libraries import Libraries


log = logging.getLogger(__name__)


class Users(db.Model, UserMixin):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(String(32), nullable=False)
    password: Mapped[str] = mapped_column(String(64), nullable=True)
    email: Mapped[str] = mapped_column(String(64), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    unlimited_access: Mapped[bool] = mapped_column(Boolean, default=False)
    bio: Mapped[Optional[str]] = mapped_column(String(75), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now, default=datetime.now, nullable=False)

    locale: Mapped[str] = mapped_column(String(8), nullable=False, default=DEFAULT_LOCALE)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    logins: Mapped[list] = mapped_column(PickleType, nullable=False, default=list)

    current_library: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    libraries: Mapped[list["Libraries"]] = relationship("Libraries", back_populates="user", cascade="save-update")
    favorite_libraries: Mapped[list["Libraries"]] = relationship("Libraries", secondary="favorites",back_populates="favorite_users")
    
    # Verification fields
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Discord fields
    discord_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    discord_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)

    # Google fields
    google_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    
    
    def __init__(self, username: str, password: Optional[str], email: str, is_admin: bool=False,
                 unlimited_access: bool=False, locale: Optional[str]=None, avatar_url: Optional[str]=None,
                 discord_token: Optional[str]=None, discord_id: Optional[str]=None,
                 google_token: Optional[str]=None, google_id: Optional[str]=None):
        
        self.username = username
        self.password = hash_password(password) if password else None
        self.email = email
        self.is_admin = is_admin
        self.unlimited_access = unlimited_access
        
        self.locale = locale or self.locale
        self.avatar_url = avatar_url or self.avatar_url
        
        # Discord fields
        self.discord_token = discord_token
        self.discord_id = discord_id
        
        # Google fields
        self.google_token = google_token
        self.google_id = google_id
        
    
    def __repr__(self):
        return f"<{'Admin' if self.is_admin else 'User'} {self.username} (id={self.id})>"
    
    
    def set_avatar(self, avatar: str | FileStorage) -> None:
        """
        Set the user's avatar.
        """
        
        filename = f"{hashlib.sha256(self.email.encode()).hexdigest()}.png"
        path = os.path.join(DEFAULT_AVATAR_FOLDER, filename)
        
        if type(avatar) in [str, FileStorage]:
            if os.path.exists(os.path.join(BASEDIR, "static", path)):
                os.remove(os.path.join(BASEDIR, "static", path))

        if isinstance(avatar, FileStorage):
            process_image(avatar, filename)
            log.debug(f"Avatar image processed and saved to {filename}.")
            
        elif isinstance(avatar, str):
            try:
                resp = requests.get(avatar, stream=True)
                resp.raise_for_status()
                
                if resp.headers.get("Content-Type", "").startswith("image/"):
                    os.remove(os.path.join(BASEDIR, "static", DEFAULT_AVATAR_FOLDER, filename))
                    process_image(io.BytesIO(resp.content), filename)
                    log.debug(f"Avatar image downloaded and processed from {avatar}.")
                    
                else:
                    log.error(f"Invalid image URL: {avatar}")
                    return None
                
            except requests.RequestException as e:
                log.error(f"Failed to download image from {avatar}: {e}")
                return None
    
        if os.path.exists(os.path.join(BASEDIR, "static", path)):
            self.avatar_url = url_for("static", filename=path)
            db.session.commit()
            
            log.debug(f"Avatar URL set to {self.avatar_url}.")
            
        else:
            self.avatar_url = url_for("static", filename=os.path.join(DEFAULT_AVATAR_FOLDER, DEFAULT_AVATAR))
    
    
    def set_password(self, password: str) -> None:
        """
        Set a new password for the user.
        
        Parameters
        ----------
        password : str
            The new password to set.
        """
        self.password = hash_password(password)
        db.session.commit()
    
    
    def check_password(self, password) -> bool:
        """
        Check if the provided password matches the stored password.
        
        Parameters
        ----------
        password : str
            The password to check.
        
        Returns
        -------
        bool
            True if the password matches, False otherwise.
        """
        return check_password(self.password, password)
    
    
    def update_login_info(self) -> None:

        if not self.logins:
            self.logins = []
            
        self.logins.append({
            "ip": request.remote_addr,
            "time": datetime.now().strftime(DATETIME_FORMAT),
        })
    
    
    def update(self, data: dict) -> None:
        """
        Update the user with the provided data.
        
        Parameters
        ----------
        data : dict
            The data to update the user with.
        """
        for key, value in data.items():
            if hasattr(self, key):
                if key == "password":
                    setattr(self, key, hash_password(value))
                else:
                    setattr(self, key, value)
        
        db.session.commit()
