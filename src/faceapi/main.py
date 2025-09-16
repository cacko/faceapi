import logging
import os
from corefile import TempPath
from fastapi import FastAPI
from faceapi.core.queue import GeneratorQueue
from faceapi.core.scheduler import Scheduler
from faceapi.database.database import Database
from .routers import api
from fastapi.middleware.cors import CORSMiddleware
from faceapi.config import app_config
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from faceapi.core.generator import Generator
import signal
from apscheduler.schedulers.background import BackgroundScheduler
from faceapi.core.jobs import update_options, update_access

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def create_app():
    app = FastAPI(
        title="face@cacko.net",
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


queue = GeneratorQueue()
generator_worker = Generator(queue=queue)
generator_worker.start()

scheduler = Scheduler(BackgroundScheduler(), app_config.redis.url)


if not Scheduler.is_running:
    Scheduler.add_job(
        id="update_options",
        func=update_options,
        trigger="interval",
        minutes=10,
        misfire_grace_time=300,
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    Scheduler.add_job(
        id="update_access",
        func=update_access,
        trigger="interval",
        minutes=10,
        misfire_grace_time=300,
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    Scheduler.start()


def handler_stop_signals(signum, frame):
    generator_worker.stop()
    Database.db.close()
    Scheduler.stop()
    TempPath.clean()
    raise RuntimeError


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)
