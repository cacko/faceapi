import logging
from typing import Any, Optional
from .service_account import ServiceAccount
import firebase_admin
import firebase_admin.auth
from pydantic import BaseModel


class AuthUser(BaseModel):
    exp: int
    uid: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


class AuthMeta(type):
    _instance: Optional['Auth'] = None

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwds)
        return cls._instance


class Auth(object, metaclass=AuthMeta):

    def verify_token(self, token: str) -> AuthUser:
        res = firebase_admin.auth.verify_id_token(
            token,
            app=ServiceAccount.app
        )
        logging.debug(f"auth user {res}")
        return AuthUser(**res)
