from sqlalchemy import create_engine
from sqlalchemy.orm import registry

mapper_registry = registry()
engine = create_engine("sqlite+pysqlite:///database.db", echo=True, future=True)