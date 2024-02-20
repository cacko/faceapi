from email.policy import default
import logging
from typing import Optional
from venv import create

from sympy import EX, GeneratorsNeeded

from faceapi.database.enums import ImageType, Status
from faceapi.masha.face2img import Face2Img

from faceapi.database.models.image import Image

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
from playhouse.signals import Model, post_save
from faceapi.firebase.db import GeneerationDb


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
    Status = StatusField(default=Status.STARTED)
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
        self.last_modified = datetime.datetime.now(tz=datetime.timezone.utc)
        self.save(only=["deleted", "last_modified"])

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
        return super().save(*args, **kwds)

    def generate(self) -> bool:
        if self.Status:
            return True
        try:
            client = Face2Img(
                img_path=self.source.tmp_path,
                template=self.template,
                model=self.model,
                prompt=self.prompt,
                num_inferance_steps=self.num_inferance_steps,
                guidance_scale=self.guidance_scale,
                scale=self.scale,
                clip_skip=self.clip_skip,
                width=self.width,
                height=self.height,
            )
            result = client.result()
            assert result
            img, _ = Image.get_or_create(
                Type=ImageType.GENERATED, Image=result.as_posix(), hash=file_hash(result)
            )
            self.image = img
            return self.save(only=["image"])
        except Exception as e:
            logging.exception(e)
            self.error = str(e)
            return self.save(only=["error"])
            


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
            errro=self.error
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


@post_save(sender=Generated)
def on_save_handler(model_class, instance: Generated, created):
    fdb = GeneerationDb(uid=instance.uid)
    fdb.status(
        slug=instance.slug,
        status=instance.Status
    )
