from sqlalchemy import String, Boolean, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class StationOfTheDay(Base):
    __tablename__ = "stations"

    country: Mapped[str] = mapped_column(String)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    inactive: Mapped[bool] = mapped_column(Boolean)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    title: Mapped[str] = mapped_column(String)

    def __repr__(self):
        return (
            f"StationOfTheDay(id={self.id}, title={self.title}, country={self.country}, inactive={self.inactive},"
            f" lat={self.lat}, lon={self.lon})"
        )


class RegisteredChannels(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    def __repr__(self):
        return f"RegisteredChannels(id={self.id})"
