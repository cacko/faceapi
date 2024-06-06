from pathlib import Path
from PIL import Image
from corefile import TempPath
import httpx
import logging

async def download_image(url: str, resize=True) -> TempPath:
    client = httpx.AsyncClient()
    url_path = Path(url)
    tmp_file = TempPath(f"uploaded_file_{url_path.name}")
    async with client.stream("GET", url) as r:
        with tmp_file.open("wb") as out_file:
            async for chunk in r.aiter_raw():
                n = out_file.write(chunk)
    if resize:
        img = Image.open(tmp_file.as_posix())
        img.thumbnail((1024,1024))
        img.save(tmp_file.as_posix())
    return tmp_file