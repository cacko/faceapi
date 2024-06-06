from pathlib import Path
from corefile import TempPath
import httpx
import logging

async def download_image(url: str) -> TempPath:
    client = httpx.AsyncClient()
    url_path = Path(url)
    tmp_file = TempPath(f"uploaded_file_{url_path.name}")
    logging.warn(tmp_file)
    logging.warn(url)
    async with client.stream("GET", url) as r:
        with tmp_file.open("wb") as out_file:
            async for chunk in r.aiter_raw():
                n = out_file.write(chunk)
                logging.warn(f"written {n} bytes")
    return tmp_file