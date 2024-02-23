from pydantic import BaseModel
from enum import StrEnum


class ENDPOINT(StrEnum):
    FACE2IMG = "image/face2img"
    FACE2IMG_OPTIONS = "image/face2img-options"

