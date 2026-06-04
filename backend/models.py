from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime

from datetime import datetime

from database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String)

    container_id = Column(String)

    container_name = Column(String)

    xpra_port = Column(Integer)

    status = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    last_activity = Column(DateTime, default=datetime.utcnow)

    internal_host = Column(String)

    internal_port = Column(Integer)
