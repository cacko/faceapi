import logging
from typing import Any, Optional
from cachable.request import Method, Request
from pathlib import Path
from fastapi import HTTPException
import filetype
from functools import reduce
import json
from faceapi.config import app_config
from uuid import uuid4
from corefile import TempPath

from faceapi.masha.models import ENDPOINT, APIError


class Client:

    def __make_request(
        self,
        path: str,
        json_data: dict = {},
        attachment: Path = None,
        method: Method = Method.POST,
    ):
        params: dict = {}
        if attachment:
            kind = filetype.guess(attachment.as_posix())
            fp = attachment.open("rb")
            assert kind
            params["files"] = {
                "file": (
                    f"{attachment.stem}.{kind.extension}",
                    fp,
                    kind.mime,
                    {"Expires": "0"},
                )
            }
            form_data = reduce(
                lambda r, x: {
                    **r,
                    **(
                        {x: json_data.get(x)}
                        if json_data.get(x, None) is not None
                        else {}
                    ),
                },
                json_data.keys(),
                {},
            )
            params["data"] = {**form_data, "data": json.dumps(form_data)}
            logging.debug(params)
        else:
            params["json"] = reduce(
                lambda r, x: {
                    **r,
                    **(
                        {x: json_data.get(x)}
                        if json_data.get(x, None) is not None
                        else {}
                    ),
                },
                json_data.keys(),
                {},
            )
            logging.debug(params["json"])

        extra_headers = {}

        return Request(
            f"http://{app_config.masha.host}:{app_config.masha.port}/{path}",
            method=method,
            extra_headers=extra_headers,
            **params,
        )

    def getResponse(
        self,
        path: str,
        data: dict = {},
        attachment: Path = None,
        method=Method.POST,
    ):
        req = self.__make_request(
            path=path, json_data=data, attachment=attachment, method=method
        )
        if req.status > 400:
            raise APIError(req.status, req.json().get("detail"))
        message = ""
        attachment = None
        is_multipart = req.is_multipart
        if is_multipart:
            multipart = req.multipart
            for part in multipart.parts:
                content_type = part.headers.get(
                    b"content-type",  # type: ignore
                    b"",  # type: ignore
                ).decode()
                if "image/png" in content_type:
                    fp = TempPath(f"{uuid4().hex}.png")
                    fp.write_bytes(part.content)
                    attachment = fp
                elif "image/jpeg" in content_type:
                    fp = TempPath(f"{uuid4().hex}.jpg")
                    fp.write_bytes(part.content)
                    attachment = fp
                elif "image/webp" in content_type:
                    fp = TempPath(f"{uuid4().hex}.webp")
                    fp.write_bytes(part.content)
                    attachment = fp

                else:
                    message = part.text
        else:
            try:
                message = req.json
            except json.JSONDecodeError as e:
                logging.error(e)
                raise e
        return attachment, message
