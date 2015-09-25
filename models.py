import json
import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from encoder import AlchemyEncoder
from settings import settings

__author__ = 'denself'


Base = declarative_base()
Base.json = lambda self: json.dumps(self, cls=AlchemyEncoder)


class Backend(object):
    def __init__(self):
        engine = sa.create_engine(settings.DB_URL, pool_recycle=3600)
        self._session = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)

    @classmethod
    def instance(cls):
        """Singleton like accessor to instantiate backend object"""
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def get_session(self):
        return self._session()


class LogEntry(Base):

    __tablename__ = u'log_entry'
    __table_args__ = {}

    id = sa.Column('id', sa.String(32), primary_key=True,
                   default=lambda: uuid.uuid4().hex)
    imei = sa.Column('imei', sa.String(40))
    latitude = sa.Column('latitude', sa.Float())
    longitude = sa.Column('longitude', sa.Float())
    altitude = sa.Column('altitude', sa.Float())
    gps_utc_time = sa.Column('gps_utc_time', sa.Integer)
    speed = sa.Column('speed', sa.Float())
    dt_create = sa.Column('dt_create', sa.DateTime, default=datetime.utcnow)

