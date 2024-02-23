import json
from typing import Optional
from faceapi.database.fields import CleanCharField, CleanTextField
from .base import DbModel
from faceapi.database import Database
from faceapi.routers.models import PromptResponse
from peewee import (
    FloatField,
    IntegerField
)

class Prompt(DbModel):
    uid = CleanCharField()
    model = CleanCharField()
    prompt = CleanTextField(null=True)
    template = CleanCharField(null=True)
    num_inference_steps = IntegerField(null=True)
    negative_prompt = CleanTextField(null=True)
    guidance_scale = FloatField(null=True)
    scale = FloatField(null=True)
    clip_skip = IntegerField(null=True)
    
    @classmethod
    def to_string(
        cls, 
        model: str=None,
        prompt: str=None,
        negative_prompt: str = None,
        template: str=None,
        num_inference_steps: int = None,
        guidance_scale: float = None,
        scale: float = None,
        clip_skip: int = None
    ) -> str:
        res = ""
        if model:
            res += f" -m {model}"
        if prompt:
            res += f' -p "{prompt}"'
        if template:
            res += f" -t {template}"
        
        return res.strip()
        
        
    

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_response(self, **kwds):
        return PromptResponse(**self.to_dict())

    class Meta:
        database = Database.db
        table_name = 'face_prompt'
        indexes = (
            (('uid',), True),
        )
