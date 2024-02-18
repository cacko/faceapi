from fastapi.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN
from faceapi.firebase.auth import Auth
import logging


ALLOWED_IPS = ["127.0.0.1"]


class Authorization:

    async def __call__(self, request: Request):
        try:
            client = request.client
            assert client
            logging.info(f"auth -> {client.host}")
            if client.host in ALLOWED_IPS:
                return
            token = request.headers.get("x-user-token", "")
            logging.debug(f"token from header {token}")
            assert token
            auth_user = Auth().verify_token(token)
            assert auth_user
            return auth_user
        except AssertionError:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )


check_auth = Authorization()
