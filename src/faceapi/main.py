import os
from fastapi import FastAPI

from faceapi.core.queue import GeneratorQueue
from .routers import api
from fastapi.middleware.cors import CORSMiddleware
from faceapi.config import app_config
from hypercorn.config import Config
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from faceapi.core.generator import Generator
import signal
import trio
from hypercorn.trio import serve as hypercorn_serve

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


def serve():
    server_config = Config.from_mapping(
        bind=f"{app_config.api.host}:{app_config.api.port}",
        worker_class="trio",
        accesslog="-",
        errorlog="-",
        loglevel=os.environ.get("FACE_LOG_LEVEL", "INFO"),
    )
    trio.run(hypercorn_serve, create_app(), server_config)


queue = GeneratorQueue()
generator_worker = Generator(queue=queue)
generator_worker.start()


def handler_stop_signals(signum, frame):
    generator_worker.stop()
    raise RuntimeError


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)
