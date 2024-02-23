from functools import lru_cache
import logging
from pathlib import Path
import time
from faceapi.masha.models import ENDPOINT
from .client import Client
from corestring import string_hash
from cachable.request import Method


class Face2Img(Client):

    def __init__(self, img_path: Path, **kwds) -> None:
        self.__img_path = img_path
        self.__prompt = kwds
        super().__init__()

    def result(self):
        img, msg = self.getResponse(
            path=f"{ENDPOINT.FACE2IMG}/{string_hash(self.__img_path.as_posix(), time.time())}",
            data=self.__prompt,
            attachment=self.__img_path,
        )
        logging.info(msg)
        return img


class Face2ImgOptions(Client):

    @lru_cache()
    def result(self):
        _, result = self.getResponse(
            path=f"{ENDPOINT.FACE2IMG_OPTIONS}", method=Method.GET
        )
        return result
