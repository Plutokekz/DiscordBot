from database.database import mapper_registry, engine
from sqlalchemy import Column, Integer, String, DateTime

Base = mapper_registry.generate_base()


class SongRequest(Base):
    __tablename__ = "songrequest"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    web_page = Column(String)
    requester_id = Column(String)
    date = Column(DateTime)

    def __repr__(self):
        return f"SongRequest(id={self.id!r}, title={self.title!r}, web_page={self.web_page!r}," \
               f" requester={self.requester!r}, date={self.date!r})"


mapper_registry.metadata.create_all(engine)
