from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class AgentsBase(DeclarativeBase):
    metadata = MetaData(schema="agents")
