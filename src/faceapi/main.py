import logging
import os
from fastapi import FastAPI

from faceapi.core.queue import GeneratorQueue
from faceapi.core.scheduler import Scheduler
from faceapi.database.database import Database
from .routers import api
from fastapi.middleware.cors import CORSMiddleware
from faceapi.config import app_config
import uvicorn
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from faceapi.core.generator import Generator
import signal
from apscheduler.schedulers.background import BackgroundScheduler
from faceapi.core.jobs import update_options

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def create_app():
    app = FastAPI(
        title="jobs@cacko.net",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url="/api/redoc",
    )

    origins = [
        "http://localhost:4200",
        "https://face.cacko.net",
        "https://facision.web.app",
        "https://facision.firebaseapp.com",
    ]

    assets_path = Path(app_config.api.assets)
    if not assets_path.exists():
        assets_path.mkdir(parents=True, exist_ok=True)

    app.mount(
        "/api/assets", StaticFiles(directory=assets_path.as_posix()), name="assets"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-pagination-page", "x-pagination-total", "x-pagination-next"],
    )

    app.include_router(api.router)
    return app


server_config = uvicorn.Config(
    app=create_app(),
    host=app_config.api.host,
    port=app_config.api.port,
    use_colors=True,
    workers=app_config.api.workers,
    log_level=logging._nameToLevel.get(os.environ.get("FACE_LOG_LEVEL", "INFO")),
)
server = uvicorn.Server(server_config)

queue = GeneratorQueue()
generator_worker = Generator(queue=queue)
generator_worker.start()

scheduler = Scheduler(BackgroundScheduler(), app_config.redis.url)

Scheduler.add_job(
    id="update_options",
    func=update_options,
    trigger="interval",
    minutes=60,
    misfire_grace_time=900,
    max_instances=1,
    coalesce=True,
    replace_existing=True,
)

Scheduler.start()


def handler_stop_signals(signum, frame):
    generator_worker.stop()
    Database.db.close_all()
    Scheduler.stop()
    server.shutdown()
    raise RuntimeError


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)


def serve():
    server.run()
