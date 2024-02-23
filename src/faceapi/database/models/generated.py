import logging
from typing import Optional
from playhouse.signals import post_save
from faceapi.database.enums import Status

from faceapi.database.models.image import Image
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
    IntegerField,
    FloatField,
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
    prompt = CleanCharField(null=True)
    model = CleanCharField(null=True)
    template = CleanCharField(null=True)
    num_inferance_steps = IntegerField(null=True)
    guidance_scale = FloatField(null=True)
    scale = FloatField(null=True)
    clip_skip = IntegerField(null=True)
    width = IntegerField(null=True)
    height = IntegerField(null=True)
    image = ForeignKeyField(Image, null=True)
    source = ForeignKeyField(Image)
    last_modified = DateTimeField(default=datetime.datetime.now)
    Status = StatusField(default=Status.PENDING)
    error = CleanCharField(null=True)
    deleted = BooleanField(default=False)

    @classmethod
    def get_slug(cls, **kwds) -> Optional[str]:
        prompt = [kwds.get("prompt", "")]
        prompt.append(kwds.get("model", ""))
        prompt.append(kwds.get("template", ""))
        prompt.append(kwds.get("num_inferance_steps", ""))
        prompt.append(kwds.get("guidance_scale", ""))
        prompt.append(kwds.get("scale", ""))
        prompt.append(kwds.get("clip_skip", ""))
        prompt.append(kwds.get("width", ""))
        prompt.append(kwds.get("height", ""))
        uid = kwds.get("uid")
        assert uid
        source = kwds.get("source")
        assert source
        return string_hash(
            f"{source.hash}-{'-'.join(map(str, filter(None, prompt)))}-{uid}"
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

    def delete_instance(self, recursive=False, delete_nullable=False):
        self.deleted = True
        self.save(only=["deleted"])

    def save(self, *args, **kwds):
        if not self.slug:
            self.slug = self.__class__.get_slug(
                prompt=self.prompt,
                model=self.model,
                template=self.template,
                source=self.source,
                uid=self.uid,
                num_inferance_steps=self.num_inferance_steps,
                guidance_scale=self.guidance_scale,
                scale=self.scale,
                clip_skip=self.clip_skip,
                width=self.width,
                height=self.height,
            )
        self.last_modified = datetime.datetime.now(tz=datetime.timezone.utc)
        ret = super().save(*args, **kwds)
        fdb = GeneerationDb(uid=self.uid)
        fdb.status(
            slug=self.slug,
            status=self.Status
        )
        return ret


    def to_response(self, **kwds):
        return GeneratedReponse(
            slug=self.slug,
            uid=self.uid,
            prompt=self.prompt,
            model=self.model,
            template=self.template,
            num_inferance_steps=self.num_inferance_steps,
            guidance_scale=self.guidance_scale,
            scale=self.scale,
            clip_skip=self.clip_skip,
            width=self.width,
            height=self.height,
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

