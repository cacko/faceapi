import logging
from typing import Any, Optional

from faceapi.database.enums import Status
from firebase_admin import db


class DbMeta(type):
    _instance: Optional["Db"] = None

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        cls._instance = type.__call__(cls, *args, **kwds)


class GeneerationDb(object, metaclass=DbMeta):

    def __init__(
        self,
        uid: str,
    ):
        self.__uid = uid

    @property
    def root_ref(self):
        return db.reference(f"generation/{self.__uid}")

    def status(self, slug: str, status: Status):
        status_ref = self.root_ref.child("slug")
        return status_ref.set(dict(status=status.valuke))
