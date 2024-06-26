import logging
from requests_toolbelt import MultipartEncoder
from pathlib import Path
from fastapi import Response, UploadFile
from corefile import TempPath
import filetype
from typing import Optional


def make_response(image_path: Optional[Path] = None, message: Optional[str] = None):
    if image_path:
        return make_multipart_response(image_path, message)
    return {"response": message}


def make_multipart_response(image_path: Path, message: Optional[str] = None):
    assert image_path.exists()
    kind = filetype.guess(image_path.as_posix())
    assert kind
    m = MultipartEncoder(
        fields={
            "message": message if message else "",
            "file": (image_path.name, image_path.open("rb"), kind.mime),
        }
    )
    logging.info(m.content_type)
    return Response(m.to_string(), media_type=m.content_type)


async def uploaded_file(file: UploadFile) -> Path:
    tmp_path = TempPath(f"uploaded_file_{file.filename}")
    tmp_path.write_bytes(await file.read())
    return tmp_path
