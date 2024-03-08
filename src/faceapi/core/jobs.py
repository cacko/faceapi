import logging
from xml.dom.pulldom import PullDOM
from faceapi.firebase.db import OptionsDb, AccessDb
from faceapi.masha.face2img import Face2ImgOptions
from faceapi.config import app_config 


def update_options():
    api = Face2ImgOptions()
    result = api.result()
    logging.info(result)
    OptionsDb().options(**result)
    

def update_access():
    AccessDb().access(**app_config.access.model_dump())
    