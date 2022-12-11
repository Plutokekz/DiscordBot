from sqlalchemy import Column, Integer
from database.database import mapper_registry, engine

Base = mapper_registry.generate_base()


class RegisteredChannelWithMessageId(Base):
    __tablename__ = "channels-with-message-id"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer)

    def __repr__(self):
        return f"RegisteredChannelWithMessageId(id={self.id}, message_id={self.message_id})"


mapper_registry.metadata.create_all(engine)
