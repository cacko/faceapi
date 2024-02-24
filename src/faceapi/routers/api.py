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
from faceapi.core.commands import Command
from faceapi.core.queue import GeneratorQueue
from faceapi.database.enums import ImageType, Status
from faceapi.database.models import Generated, Image
from fastapi.responses import JSONResponse
from datetime import datetime

from faceapi.masha.face2img import Face2ImgOptions
from .auth import check_auth
from faceapi.config import app_config
from corestring import file_hash
from faceapi.core.api import uploaded_file
import json
from starlette.concurrency import run_in_threadpool

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


# @router.get("/api/jobs", tags=["api"])
# def list_jobs(
#     page: int = 1,
#     limit: int = 30,
#     last_modified: Optional[datetime] = None,
#     auth_user=Depends(check_auth)
# ):
#     return get_list_response(
#         page=page,
#         limit=limit,
#         last_modified=last_modified
#     )


@router.get("/api/generated", tags=["api"])
def api_generations(
    page: Annotated[int, Query()] = 1,
    limit: Annotated[int, Query()] = 20,
    last_modified: Annotated[datetime, Query()] = None,
    auth_user=Depends(check_auth),
):
    try:
        return get_list_response(
            page=page, limit=limit, last_modified=last_modified, uid=auth_user.uid
        )
    except:
        raise HTTPException(404)


@router.get("/api/generated/{slug}", tags=["api"])
async def api_generated(
    slug: Annotated[str, Path(title="generation id")], auth_user=Depends(check_auth)
):
    try:
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
async def api_generated_delete(
    slug: Annotated[str, Path(title="generation id")], auth_user=Depends(check_auth)
):
    try:
        record: Generated = (
            Generated.select(Generated)
            .where((Generated.slug == slug) & (Generated.uid == auth_user.uid))
            .get()
        )
        record.delete_instance()
        assert record
        response = record.to_response()
        return response.model_dump()
    except AssertionError:
        raise HTTPException(404)


@router.post("/api/generate", tags=["api"])
async def api_generate(
    file: Annotated[UploadFile, File()],
    data: Annotated[str, Form()],
    auth_user=Depends(check_auth),
):
    face_path = await uploaded_file(file)
    data_json = json.loads(data)
    source, _ = Image.get_or_create(
        Type=ImageType.SOURCE,
        Image=face_path.as_posix(),
        hash=file_hash(face_path),
    )
    generated, _ = Generated.get_or_create(
        uid=auth_user.uid, source=source, **data_json
    )
    if generated.Status != Status.GENERATED:
        generated.Status = Status.PENDING
        generated.save(only=["Status"])
        GeneratorQueue().put_nowait((Command.GENERATE, generated.slug))
    generated.deleted = False
    generated.save(only=["deleted"])
    return generated.to_response().model_dump()


@router.get("/api/options", tags=["api"])
async def api_options(
    auth_user=Depends(check_auth),
):
    api = Face2ImgOptions()
    return api.result()