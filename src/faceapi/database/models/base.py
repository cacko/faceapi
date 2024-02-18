from peewee import Model, DoesNotExist
from playhouse.shortcuts import model_to_dict
from humanfriendly.tables import format_robust_table

from faceapi.routers.models import BaseResponse


class DbModel(Model):
    @classmethod
    def fetch(cls, *query, **filters):
        try:
            return cls.get(*query, **filters)
        except DoesNotExist:
            return None

    def to_dict(self):
        return model_to_dict(self)

    def to_response(self, **kwds) -> BaseResponse:
        raise NotImplementedError

    def to_table(self):
        data = self.to_dict()
        columns = list(data.keys())
        values = list(data.values())
        return format_robust_table(
            [values],
            column_names=columns
        )
