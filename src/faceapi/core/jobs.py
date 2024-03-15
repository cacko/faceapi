import logging
from faceapi.database.models.generated import Generated
from faceapi.firebase.db import OptionsDb, AccessDb
from faceapi.masha.face2img import Face2ImgOptions
from faceapi.config import app_config

from faceapi.database.enums import Status


def update_options():
    api = Face2ImgOptions()
    result = api.result()
    logging.info(result)
    OptionsDb().options(**result)


def update_access():
    AccessDb().access(**app_config.access.model_dump())


def resume_generations():

    base_query = Generated.select(Generated.slug)
    query = base_query.where(
        Generated.Status.in_([Status.PENDING, Status.IN_PROGRESS])
    ).order_by(Generated.last_modified.asc())
    for slug in query.get():
        print(slug)
