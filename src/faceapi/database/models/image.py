from pathlib import Path

from attr import has
from .base import DbModel
from faceapi.database import Database
from faceapi.database.fields import ImageTypeField, ImageField
from peewee import (
    CharField,
    DateTimeField,
    BooleanField,
    IntegrityError,
)
from faceapi.config import app_config
import datetime


class Image(DbModel):
    hash = CharField()
    Type = ImageTypeField()
    Image = ImageField()
    last_modified = DateTimeField(default=datetime.datetime.now)
    deleted = BooleanField(default=False)

    @classmethod
    def get_or_create(cls, **kwargs) -> tuple["Image", bool]:
        defaults = kwargs.pop("defaults", {})
        query = cls.select()
        hash = kwargs.get("hash")
        query = query.where((cls.hash == hash) & (cls.deleted == False))

        try:
            return query.get(), False
        except cls.DoesNotExist:
            try:
                with cls._meta.database.atomic():
                    if defaults:
                        kwargs.update(defaults)
                    return cls.create(**kwargs), True
            except IntegrityError as exc:
                try:
                    return query.get(), False
                except cls.DoesNotExist:
                    raise exc

    def delete_instance(self, recursive=False, delete_nullable=False):
        self.deleted = True
        self.last_modified = datetime.datetime.now(tz=datetime.timezone.utc)
        self.save(only=["deleted", "last_modified"])

    def save(self, *args, **kwds):
        if "only" not in kwds:
            self.last_modified = datetime.datetime.now(tz=datetime.timezone.utc)
        return super().save(*args, **kwds)

    @property
    def tmp_path(self) -> Path:
        raw_src = ImageField.raw_src(Path(self.Image))
        key = Path(raw_src).name
        return ImageField.download(key)

    def to_response(self, **kwds):
        return ImageField.to_response(image=self.Image, hash=self.hash)

    class Meta:
        database = Database.db
        table_name = "face_image"
        order_by = ["-last_modified"]
        indexes = ((("hash", "Type"), False),)


# JobSkill = Job.skills.get_through_model()
