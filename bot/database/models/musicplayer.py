from datetime import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class SongRequest(Base):
    __tablename__ = "songrequest"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    web_page: Mapped[str] = mapped_column(String)
    requester_id: Mapped[str] = mapped_column(String)
    server_id: Mapped[str] = mapped_column(String)
    date: Mapped[datetime] = mapped_column(DateTime)

    def __repr__(self):
        return (
            f"SongRequest(id={self.id!r}, title={self.title!r}, web_page={self.web_page!r},"
            f" requester={self.requester_id!r}, server_id={self.server_id!r}, date={self.date!r})"
        )
