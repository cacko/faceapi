from pydantic import BaseModel
from enum import StrEnum


class ENDPOINT(StrEnum):
    FACE2IMG = "image/face2img"
    FACE2IMG_OPTIONS = "image/face2img-options"
    IMG2IMG = "image/img2img"


class APIError(Exception):
    
    def __init__(self, code: int, message: str, *args: object) -> None:
        self.message = message
        self.code = code
        super().__init__(*args)