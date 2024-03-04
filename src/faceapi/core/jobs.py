import logging
from faceapi.firebase.db import OptionsDb
from faceapi.masha.face2img import Face2ImgOptions

def update_options():
    api = Face2ImgOptions()
    result = api.result()
    logging.info(result)
    OptionsDb().options(**result)