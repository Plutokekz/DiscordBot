from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    pass


class RegisteredChannelWithMessageId(Base):
    __tablename__ = "channels-with-message-id"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer)

    def __repr__(self):
        return f"RegisteredChannelWithMessageId(id={self.id}, message_id={self.message_id})"
