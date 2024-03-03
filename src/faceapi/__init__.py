__name__ = "faceapi"
__version__ = "0.0.1"

import corelog
import os


corelog.register(
    os.environ.get("FACE_LOG_LEVEL", "DEBUG"), handler_type=corelog.Handlers.DEFAULT
)

import logging

logger = logging.getLogger("peewee")
logger.addHandler(logging.StreamHandler())
logger.setLevel(
    os.environ.get("FACE_LOG_LEVEL", "DEBUG"),
)
