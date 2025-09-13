import logging
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db

if TYPE_CHECKING:
    from .libraries import Libraries


log = logging.getLogger(__name__)


class Words(db.Model):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chinese: Mapped[str] = mapped_column(String(32), nullable=False)
    english: Mapped[str] = mapped_column(String(32), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now, default=datetime.now, nullable=False)
    
    _library_id: Mapped[int] = mapped_column("library_id", ForeignKey("libraries.id"), nullable=True)
    library: Mapped["Libraries"] = relationship("Libraries", back_populates="words")

    def __init__(self, chinese: str, english: str):
        self.chinese = chinese
        self.english = english

    def __repr__(self) -> str:
        return f"<{self.chinese}: {self.english}, from 《{self.library.name if self.library else 'No Library'}》>"
