from playhouse.db_url import parse
from peewee import PostgresqlDatabase
from playhouse.shortcuts import ReconnectMixin, OperationalError, InterfaceError
from faceapi.config import app_config
from typing import Optional, Any
from psycopg2 import OperationalError


class ReconnectingDB(ReconnectMixin, PostgresqlDatabase):

    reconnect_errors = (
        (OperationalError, "terminat"),
        (InterfaceError, "connection already closed"),
    )


class DatabaseMeta(type):
    _instance: Optional["Database"] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    @property
    def db(cls) -> ReconnectingDB:
        return cls().get_db()


class Database(object, metaclass=DatabaseMeta):

    def __init__(self):
        parsed = parse(app_config.db.url)
        self.__db = ReconnectingDB(**parsed)

    def get_db(self) -> ReconnectingDB:
        return self.__db
