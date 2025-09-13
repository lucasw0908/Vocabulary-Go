import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from . import db


log = logging.getLogger(__name__)


class Sentences(db.Model):
    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chinese: Mapped[str] = mapped_column(String(256), nullable=False)
    english: Mapped[str] = mapped_column(String(256), nullable=False)
    word_chinese: Mapped[str] = mapped_column(String(32), nullable=False)
    word_english: Mapped[str] = mapped_column(String(32), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.now, default=datetime.now, nullable=False)

    def __init__(self, chinese: str, english: str, word_chinese: str, word_english: str):
        self.chinese = chinese
        self.english = english
        self.word_chinese = word_chinese
        self.word_english = word_english

    def __repr__(self) -> str:
        return f"<{self.word_english} - '{self.english}'>"
