import logging
from typing import Optional
from faceapi.database.enums import Status
from faceapi.database.models.image import Image
from faceapi.database.models.prompt import Prompt
from faceapi.firebase.db import GeneerationDb

from .base import DbModel
from faceapi.database import Database
from faceapi.database.fields import (
    CleanCharField,
    StatusField,
)
from peewee import (
    CharField,
    DateTimeField,
    BooleanField,
    IntegrityError,
    ForeignKeyField,
)
import datetime

from faceapi.routers.models import GeneratedReponse
from corestring import file_hash, string_hash



class Generated(DbModel):
    slug = CharField(unique=True)
    uid = CleanCharField()
    image = ForeignKeyField(Image, null=True)
    source = ForeignKeyField(Image)
    prompt = ForeignKeyField(Prompt)
    last_modified = DateTimeField(default=datetime.datetime.now)
    Status = StatusField(default=Status.PENDING)
    error = CleanCharField(null=True)
    deleted = BooleanField(default=False)

    @classmethod
    def get_slug(cls, **kwds) -> Optional[str]:
        prompt: Prompt = kwds.get("prompt")
        assert prompt
        uid = kwds.get("uid")
        assert uid
        source: Image = kwds.get("source")
        assert source
        return string_hash(
            f"{source.hash}-{prompt.hash}-{uid}"
        )

    @classmethod
    def get_or_create(cls, **kwargs) -> tuple["Generated", bool]:
        defaults = kwargs.pop("defaults", {})
        query = cls.select()
        slug = cls.get_slug(**kwargs)
        query = query.where(cls.slug == slug)

        try:
            return query.get(), False
        except cls.DoesNotExist:
            try:
                if defaults:
                    kwargs.update(defaults)
                with cls._meta.database.atomic():
                    return cls.create(**kwargs), True
            except IntegrityError as exc:
                try:
                    return query.get(), False
                except cls.DoesNotExist:
                    raise exc

    @classmethod
    def create(cls, **query):
        query["slug"] = cls.get_slug(**query)
        return super().create(**query)

    def delete_instance(self, recursive=False, delete_nullable=False):
        self.deleted = True
        self.save(only=["deleted"])

    def save(self, *args, **kwds):
        self.last_modified = datetime.datetime.now(tz=datetime.timezone.utc)
        ret = super().save(*args, **kwds)
        fdb = GeneerationDb(uid=self.uid)
        fdb.status(slug=self.slug, status=self.Status)
        return ret

    def to_response(self, **kwds):
        return GeneratedReponse(
            slug=self.slug,
            uid=self.uid,
            prompt=self.prompt.to_response() if self.prompt else None,
            image=self.image.to_response() if self.image else None,
            source=self.source.to_response() if self.source else None,
            last_modified=self.last_modified,
            deleted=self.deleted,
            status=self.Status,
            error=self.error,
            **kwds,
        )

    class Meta:
        database = Database.db
        table_name = "face_generated"
        order_by = ["-last_modified"]
        indexes = (
            (("uid",), False),
            (("slug",), True),
        )
