import json
from typing import Optional
from faceapi.database.fields import CleanCharField, CleanTextField
from .base import DbModel
from faceapi.database import Database
from faceapi.routers.models import PromptResponse
from peewee import FloatField, IntegerField, IntegrityError, DoubleField
from corestring import split_with_quotes, string_hash
from argparse import ArgumentParser
from pydantic import BaseModel, validator
import logging
import shlex


class FaceGeneratorParams(BaseModel):
    prompt: Optional[list[str] | str] = None
    guidance_scale: Optional[float] = None
    num_inference_steps: Optional[int] = None
    negative_prompt: Optional[str] = None
    model: Optional[str] = None
    template: Optional[str] = None
    scale: Optional[float] = None
    strength: Optional[float] = None
    clip_skip: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None

    @validator("prompt")
    def static_prompt(cls, prompt: list[str]):
        try:
            assert prompt
            return " ".join(prompt)
        except AssertionError:
            return ""


PROMPT_PARSER = ArgumentParser(
    description="Face2Image Processing", exit_on_error=False, add_help=False
)
PROMPT_PARSER.add_argument("prompt", nargs="*")
PROMPT_PARSER.add_argument("-n", "--negative_prompt", type=str)
PROMPT_PARSER.add_argument("-g", "--guidance_scale", type=float)
PROMPT_PARSER.add_argument("-i", "--num_inference_steps", type=int)
PROMPT_PARSER.add_argument("-sc", "--scale", type=float)
PROMPT_PARSER.add_argument("-m", "--model", type=str)
PROMPT_PARSER.add_argument("-t", "--template", type=str)
PROMPT_PARSER.add_argument("-cs", "--clip_skip", type=int)
PROMPT_PARSER.add_argument("-w", "--width", type=int)
PROMPT_PARSER.add_argument("-h", "--height", type=int)
PROMPT_PARSER.add_argument("-st", "--strength", type=float)
PROMPT_PARSER.add_argument("-s", "--seed", type=int)


class Prompt(DbModel):
    hash = CleanCharField(unique=True)
    model = CleanCharField(null=True)
    prompt = CleanTextField(null=True)
    template = CleanCharField(null=True)
    num_inference_steps = IntegerField(null=True)
    negative_prompt = CleanTextField(null=True)
    guidance_scale = FloatField(null=True)
    scale = FloatField(null=True)
    clip_skip = IntegerField(null=True)
    width = IntegerField(null=True)
    height = IntegerField(null=True)
    strength = FloatField(null=True)
    seed = DoubleField(null=True)

    @classmethod
    def get_hash(cls, **kwds) -> Optional[str]:
        prompt = [kwds.get("prompt", "")]
        prompt.append(kwds.get("model", ""))
        prompt.append(kwds.get("template", ""))
        prompt.append(kwds.get("num_inference_steps", ""))
        prompt.append(kwds.get("guidance_scale", ""))
        prompt.append(kwds.get("scale", ""))
        prompt.append(kwds.get("clip_skip", ""))
        prompt.append(kwds.get("width", ""))
        prompt.append(kwds.get("height", ""))
        prompt.append(kwds.get("negative_prompt", ""))
        prompt.append(kwds.get("seed", ""))
        prompt.append(kwds.get("strength", ""))
        return string_hash("-".join(map(str, filter(None, prompt))))

    @classmethod
    def get_or_create(cls, **kwargs) -> tuple["Prompt", bool]:
        defaults = kwargs.pop("defaults", {})
        query = cls.select()
        hash = cls.get_hash(**kwargs)
        query = query.where(cls.hash == hash)
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

    @classmethod
    def create(cls, **query):
        query["hash"] = cls.get_hash(**query)
        return super().create(**query)

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_response(self, **kwds):
        return PromptResponse(**self.to_dict())

    @classmethod
    def parse_prompt(cls, prompt: str) -> "Prompt":
        args = shlex.split(prompt)
        namespace, _ = PROMPT_PARSER.parse_known_args(args)
        params = FaceGeneratorParams(**namespace.__dict__).model_dump(exclude_none=True)
        return cls.get_or_create(**params)

    class Meta:
        database = Database.db
        table_name = "face_prompt"
        indexes = ((("hash",), True),)
