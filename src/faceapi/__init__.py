__name__ = "faceapi"
__version__ = "0.0.1"

import corelog
import os


corelog.register(
    os.environ.get("FACE_LOG_LEVEL", "INFO"), handler_type=corelog.Handlers.RICH
)

import logging

logger = logging.getLogger("peewee")
logger.addHandler(logging.StreamHandler())
logger.setLevel(
    os.environ.get("FACE_LOG_LEVEL", "INFO"),
)
