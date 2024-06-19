from datetime import datetime
import logging
from typing import Any, Optional

from faceapi.database.enums import Status
from faceapi.firebase.service_account import db


class GeneerationDb(object):

    def __init__(
        self,
        uid: str,
    ):
        self.__uid = uid

    @property
    def root_ref(self):
        return db.reference(f"generation/{self.__uid}")

    def status(
        self, slug: str, status: Status, last_modified: datetime, error: str = None
    ):
        status_ref = self.root_ref.child(slug)
        return status_ref.set(
            dict(
                status=status.value,
                last_modified=last_modified.isoformat(),
                error=error,
            )
        )

    def remove(self, slug: str):
        status_ref = self.root_ref.child(slug)
        return status_ref.delete()

    def get_listener(self, slug, callback):
        return self.root_ref.child(slug).listen(callback)


class OptionsDb(object):

    @property
    def root_ref(self):
        return db.reference(f"app/")

    def options(self, **kwds):
        options_ref = self.root_ref.child("options")
        return options_ref.set(kwds)


class AccessDb(object):

    @property
    def root_ref(self):
        return db.reference(f"app/")

    def access(self, **kwds):
        options_ref = self.root_ref.child("access")
        return options_ref.set(kwds)
