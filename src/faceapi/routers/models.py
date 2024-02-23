from datetime import datetime, timezone
from email.policy import default
from typing import Optional
from pydantic import AwareDatetime, BaseModel, Field

from faceapi.database.enums import ImageType, Status


class BaseResponse(BaseModel):

    def __init__(self, *args, **kwds):
        for k, v in kwds.items():
            match v:
                case datetime():
                    kwds[k] = v.astimezone(tz=timezone.utc)
        super().__init__(*args, **kwds)

    def model_dump(self, *args, **kwds):
        return super().model_dump(mode="json")


class ImageResponse(BaseResponse):
    thumb_src: str
    webp_src: str
    raw_src: str
    hash: str


class GeneratedReponse(BaseResponse):
    slug: str
    uid: str
    last_modified: AwareDatetime
    status: Status
    deleted: bool = False
    prompt: Optional[str] = None
    model: Optional[str] = None
    template: Optional[str] = None
    num_inference_steps: Optional[int] = None
    guidance_scale: Optional[float] = None
    scale: Optional[float] = None
    clip_skip: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    image: Optional[ImageResponse] = None
    source: Optional[ImageResponse] = None
    error: Optional[str] = None


class PromptResponse(BaseResponse):
    uid: str
    model: str
    prompt: Optional[str] = None
    template: Optional[str] = None
    num_inference_steps: Optional[int] = None
    guidance_scale: Optional[float] = None
    scale: Optional[float] = None
    clip_skip: Optional[int] = None
