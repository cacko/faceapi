from functools import reduce
import logging
from math import ceil, floor
from typing import Annotated, Optional
from urllib.parse import urlencode
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Form,
    File,
    Path,
    Depends,
    UploadFile,
)
from sympy import im
from faceapi.core.commands import Command
from faceapi.core.queue import GeneratorQueue
from faceapi.database.database import Database
from faceapi.database.enums import ImageType, Status
from faceapi.database.models import Generated, Image
from fastapi.responses import JSONResponse
from datetime import datetime
from peewee import DoesNotExist

from faceapi.database.models.prompt import Prompt
from faceapi.masha.face2img import Face2ImgOptions
from .auth import check_auth
from faceapi.config import app_config
from corestring import file_hash
from faceapi.core.api import uploaded_file
from faceapi.core.image import download_image
import json

router = APIRouter()


def get_list_response(
    uid: str, page: int = 1, limit: int = 50, last_modified: Optional[datetime] = None
):
    results = []
    filters = [Generated.uid == uid]
    if last_modified:
        filters.append(Generated.last_modified > last_modified)

    base_query = Generated.select()
    query = base_query.where(*filters).order_by(Generated.last_modified.desc())
    total = query.count()
    if total > 0:
        page = min(max(1, page), floor(total / limit) + 1)
    results = [rec.to_response().model_dump() for rec in query.paginate(page, limit)]
    logging.debug(results)
    headers = {
        "x-pagination-total": f"{total}",
        "x-pagination-page": f"{page}",
    }

    def get_next_url(page: int, total: int, limit: int):
        try:
            last_page = ceil(total / limit)
            page += 1
            assert last_page + 1 > page
            params = {
                k: v
                for k, v in dict(
                    page=page,
                    limit=limit,
                ).items()
                if v
            }
            return f"{app_config.api.web_host}/api/generated?{urlencode(params)}"
        except AssertionError:
            return None

    if next_url := get_next_url(
        total=total,
        page=page,
        limit=limit,
    ):
        headers["x-pagination-next"] = next_url
    return JSONResponse(content=results, headers=headers)


@router.get("/api/generated", tags=["api"])
def api_generations(
    page: Annotated[int, Query()] = 1,
    limit: Annotated[int, Query()] = 20,
    last_modified: Annotated[datetime, Query()] = None,
    auth_user=Depends(check_auth),
):
    return get_list_response(
        page=page, limit=limit, last_modified=last_modified, uid=auth_user.uid
    )


@router.get("/api/generated/{slug}", tags=["api"])
def api_generated(
    slug: Annotated[str, Path(title="generation id")], auth_user=Depends(check_auth)
):
    try:
        with Database.db.atomic():
            record = (
                Generated.select(Generated)
                .where((Generated.slug == slug) & (Generated.uid == auth_user.uid))
                .get()
            )
            assert record
            response = record.to_response()
            return response.model_dump()
    except AssertionError:
        raise HTTPException(404)


@router.delete("/api/generated/{slug}", tags=["api"])
def api_generated_delete(
    slug: Annotated[str, Path(title="generation id")], auth_user=Depends(check_auth)
):
    try:
        record: Generated = (
            Generated.select(Generated)
            .where((Generated.slug == slug) & (Generated.uid == auth_user.uid))
            .get()
        )
        with Database.db.atomic():
            record.delete_instance()
            response = record.to_response()
            return response.model_dump()
    except (AssertionError, DoesNotExist):
        raise HTTPException(404)


@router.post("/api/generate", tags=["api"])
async def api_generate(
    data: Annotated[str, Form()],
    file: Annotated[UploadFile, File()] = None,
    auth_user=Depends(check_auth),
):
    face_path = None
    data_json = json.loads(data)
    reuse = True
    try:
        assert file
        face_path = await uploaded_file(file)
    except AssertionError:
        image_url = data_json.get("image_url")
        del data_json["image_url"]
        face_path = await download_image(image_url)
        reuse = False
        if not data_json.get("seed", None):
            data_json["seed"] = -1
        logging.warn(f"fetching file from {image_url}")
    source, _ = Image.get_or_create(
        Type=ImageType.SOURCE,
        Image=face_path.as_posix(),
        hash=file_hash(face_path),
    )
    prompt, _ = Prompt.get_or_create(**data_json)
    generated, _ = Generated.get_or_create(
        uid=auth_user.uid, source=source, prompt=prompt
    )
    logging.info(f"GENERATED STATUS -> {generated.Status}, reuse={reuse}")
    if all([reuse, generated.Status == Status.GENERATED]):
        return generated.to_response().model_dump()

    with Database.db.atomic():
        generated.Status = Status.PENDING
        generated.save(only=["Status"])
    logging.info(f"GENERATED STATUS -> {generated.Status}, reuse={reuse}")
    GeneratorQueue().put_nowait((Command.GENERATE, generated.slug))
    return generated.to_response().model_dump()


@router.get("/api/access/", tags=["api"])
def api_access(auth_user=Depends(check_auth)):
    try:
        access = app_config.access.model_dump()
        return reduce(
            lambda res, topic: [
                *res,
                *([topic] if auth_user.uid in access[topic] else []),
            ],
            access.keys(),
            [],
        )
    except AssertionError:
        raise HTTPException(404)
