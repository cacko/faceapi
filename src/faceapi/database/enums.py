from enum import StrEnum


class Choices(object):

    @classmethod
    def values(cls):
        return [m.value for m in cls.__members__.values()]

    @classmethod
    def keys(cls):
        return [m.lower() for m in cls.__members__.keys()]

    @classmethod
    def members(cls):
        return cls.__members__.values()

class ImageType(Choices, StrEnum):
    SOURCE = "source"
    GENERATED = "generated"
