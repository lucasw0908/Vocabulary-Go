import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db

if TYPE_CHECKING:
    from .words import Words
    from .users import Users

log = logging.getLogger(__name__)

favorites_table = Table(
    "favorites",
    db.Model.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("library_id", Integer, ForeignKey("libraries.id", ondelete="CASCADE"), primary_key=True),
)


class Libraries(db.Model):
    __tablename__ = "libraries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=False)
    words: Mapped[list["Words"]] = relationship("Words", back_populates="library", cascade="all, delete-orphan", single_parent=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now, default=datetime.now, nullable=False)
    
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user: Mapped[Optional["Users"]] = relationship("Users", back_populates="libraries", cascade="save-update, merge, refresh-expire")
    favorite_users: Mapped[list["Users"]] = relationship("Users", secondary=favorites_table, back_populates="favorite_libraries")

    def __init__(self, name: str, description: Optional[str] = None, public: bool = False, author_id: Optional[int] = 1):
        self.name = name
        self.description = description
        self.public = public
        self.author_id = author_id

    def __repr__(self):
        return f"<{'Public' if self.public else 'Private'} {self.name} (id={self.id})>"