from corefile import TempPath
import requests
import shutil
from uuid import uuid4



def download_image(url: str) -> TempPath:
    tmp_file = TempPath(f"{uuid4()}.jpg")
    response = requests.get(url, stream=True)
    with tmp_file.open("wb") as out_file:
        shutil.copyfileobj(response.raw, out_file)
    return tmp_file
