from playhouse.db_url import parse
from playhouse.pool import PooledPostgresqlExtDatabase
from faceapi.config import app_config
from typing import Optional

class DatabaseMeta(type):
    _instance: Optional['Database'] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    @property
    def db(cls) -> PooledPostgresqlExtDatabase:
        return cls().get_db()
    
    


class Database(object, metaclass=DatabaseMeta):

    def __init__(self):
        parsed = parse(app_config.db.url)
        self.__db = PooledPostgresqlExtDatabase(**parsed, max_connections=20, stale_timeout=300)

    def get_db(self) -> PooledPostgresqlExtDatabase:
        return self.__db
