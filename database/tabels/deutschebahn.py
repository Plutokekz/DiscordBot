from sqlalchemy import Column, String, Boolean, Float, Integer
from database.database import mapper_registry, engine

Base = mapper_registry.generate_base()


class StationOfTheDay(Base):

    __tablename__ = "stations"

    country = Column(String)
    id = Column(String, primary_key=True)
    inactive = Column(Boolean)
    lat = Column(Float)
    lon = Column(Float)
    title = Column(String)


class RegisteredChannels(Base):

    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)


mapper_registry.metadata.create_all(engine)
