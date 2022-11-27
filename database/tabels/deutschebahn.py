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

    def __repr__(self):
        return f"StationOfTheDay(id={self.id}, title={self.title}, country={self.country}, inactive={self.inactive}," \
               f" lat={self.lat}, lon={self.lon})"


class RegisteredChannels(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)

    def __repr__(self):
        return f"RegisteredChannels(id={self.id})"


mapper_registry.metadata.create_all(engine)
