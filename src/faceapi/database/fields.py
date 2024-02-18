from typing import Optional
from peewee import CharField, TextField, FieldAccessor
from faceapi.core.s3 import S3
from uuid import uuid4
from pathlib import Path
from corefile import TempPath
from PIL import Image
from faceapi.routers.models import ImageResponse
from faceapi.config import app_config
from .enums import ImageType
from rich import print

CDN_ROOT = (
    f"https://{app_config.aws.cloudfront_host}" f"/{app_config.aws.media_location}"
)


class CleanCharField(CharField):

    def db_value(self, value):
        try:
            assert value
            return super().db_value(value.strip())
        except AssertionError:
            return super().db_value(value)

    def python_value(self, value):
        try:
            assert value
            return super().python_value(value.strip())
        except AssertionError:
            return super().python_value(value)


class CleanTextField(TextField):

    def db_value(self, value):
        try:
            assert value
            return super().db_value(value.strip())
        except AssertionError:
            return super().db_value(value)

    def python_value(self, value):
        try:
            assert value
            return super().python_value(value.strip())
        except AssertionError:
            return super().python_value(value)


class ImageTypeField(CharField):

    def db_value(self, value: ImageType):
        return value.value

    def python_value(self, value):
        return ImageType(value)


class ImageFieldMeta(type):

    __downloaded: dict[str, Path] = {}

    def raw_src(cls, image_path: Path) -> str:
        stem = image_path.stem
        return f"{CDN_ROOT}/{stem}.png"

    def webp_src(cls, image_path: Path) -> str:
        stem = image_path.stem
        return f"{CDN_ROOT}/{stem}.webp"

    def thumb_src(cls, image_path: Path) -> str:
        stem = image_path.stem
        return f"{CDN_ROOT}/{stem}.thumbnail.webp"

    def download(cls, key: str) -> Path:
        try:
            assert cls.__downloaded
            dld: Path | None = cls.__downloaded.get(key)
            assert dld
            assert dld.exists()
        except AssertionError:
            cls.__downloaded[key] = S3.download(key)
        return cls.__downloaded[key]

    def to_response(cls, image: str, hash: str):
        pth = Path(image)
        return ImageResponse(
            thumb_src=cls.thumb_src(pth),
            webp_src=cls.webp_src(pth),
            raw_src=cls.raw_src(pth),
            hash=hash,
        )


class ImageFieldAccessor(FieldAccessor):

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return instance.__data__.get(self.name)
        return self.field

    def __set__(self, instance, value):
        if "id" not in instance.__data__:
            image_path = Path(value)
            assert image_path.exists()
            stem = uuid4().hex

            raw_fname = f"{stem}.png"
            S3.upload(image_path, raw_fname)

            img = Image.open(image_path.as_posix())

            webp_fname = f"{stem}.webp"
            webp_path = TempPath(webp_fname)
            img.save(webp_path.as_posix())
            S3.upload(webp_path, webp_fname)

            img.thumbnail((300, 300))
            thumb_fname = f"{stem}.thumbnail.webp"
            thumb_path = TempPath(thumb_fname)
            img.save(thumb_path.as_posix())
            S3.upload(thumb_path, thumb_fname)
            value = webp_fname

        instance.__data__[self.name] = value
        instance._dirty.add(self.name)


class ImageField(CharField, metaclass=ImageFieldMeta):
    accessor_class = ImageFieldAccessor
