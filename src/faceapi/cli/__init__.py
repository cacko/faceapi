from pathlib import Path
import time
from rich import print
import typer
from faceapi.core import s3
from faceapi.core.commands import Command
from faceapi.database.enums import ImageType, Status
from faceapi.firebase.db import GeneerationDb
from firebase_admin.db import Event
from faceapi.database import Generated, Image, Prompt, create_tables
from typing_extensions import Annotated
from coreimage.terminal import print_term_image
import logging
from corestring import file_hash
from faceapi.core.queue import GeneratorQueue
from threading import Event as TEvent
from faceapi.core.jobs import update_options as job_update_options
from faceapi.core.jobs import update_access as job_update_access
from faceapi.core.jobs import resume_generations as job_resume_generations
from faceapi.config import app_config

cli = typer.Typer()


class GenerationErrorException(Exception):
    pass


class GenerationSuccessException(Exception):
    pass


class listener:

    def __init__(self, item: Generated):
        self.event = TEvent()
        self.event.set()
        self.__uid = item.uid
        self.__slug = item.slug

    def listen(self):
        db = GeneerationDb(self.__uid)
        lst = db.get_listener(self.__slug, self.clb)
        while self.event.is_set():
            time.sleep(0.5)
        lst.close()

    def clb(self, ev: Event):
        status = Status(ev.data.get("status"))
        match status:
            case Status.ERROR:
                self.event.clear()
            case Status.GENERATED:
                self.event.clear()

@cli.command()
def init_db():
    try:
        assert typer.confirm("Dropping all data?")
        create_tables(drop=True)
    except AssertionError:
        logging.info("ignored")
        
@cli.command()
def clean():
    gen_ids = [x.image.Image.split(".")[0] for x in Generated.select() if x.image]
    objs = [k["Key"] for k in s3.S3.list(dst=app_config.aws.media_location)]
    for obj in objs:
        id = obj.split("/")[-1].split(".")[0]
        if id not in gen_ids:
            print(id, obj)
            print(s3.S3.delete(obj.split("/")[-1]))
    pass
        

@cli.command()
def update_options():
    try:
        job_update_options()
    except AssertionError:
        logging.info("ignored")


@cli.command()
def resume():
    job_resume_generations()


@cli.command()
def update_access():
    try:
        job_update_access()
    except AssertionError:
        logging.info("ignored")
        
@cli.command()
def sync():
    for rec in Generated.select():
        GeneerationDb(rec.uid).status(
            slug=rec.slug,
            status=rec.Status,
            last_modified=rec.last_modified
        )

@cli.command()
def generate(
    face_path: Annotated[Path, typer.Argument()],
    template: Annotated[str, typer.Option("-t", "--template")] = None,
    model: Annotated[str, typer.Option("-m", "--model")] = None,
    prompt: Annotated[str, typer.Option("-p", "--prompt")] = None,
    num_inference_steps: Annotated[
        int, typer.Option("-i", "--num_inference_steps")
    ] = None,
    guidance_scale: Annotated[float, typer.Option("-g", "--guidance_scale")] = None,
    scale: Annotated[float, typer.Option("-sc", "--scale")] = None,
    clip_skip: Annotated[int, typer.Option("-cs", "--clip_skip")] = None,
    width: Annotated[int, typer.Option("-w", "--width")] = None,
    height: Annotated[int, typer.Option("-h", "--height")] = None,
):
    assert face_path.exists()
    source, _ = Image.get_or_create(
        Type=ImageType.SOURCE, Image=face_path.as_posix(), hash=file_hash(face_path)
    )
    prompt_obj, _ = Prompt.get_or_create(
        model=model,
        template=template,
        prompt=prompt,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        scale=scale,
        clip_skip=clip_skip,
        width=width,
        height=height,
    )
    print_term_image(image_path=face_path)
    generated, _ = Generated.get_or_create(
        uid="dev",
        source=source,
        prompt=prompt_obj
    )
    if generated.Status != Status.GENERATED:
        GeneratorQueue().put_nowait((Command.GENERATE, generated.slug))
        l = listener(generated)
        l.listen()
        generated: Generated = (
            Generated.select().where(Generated.slug == generated.slug).get()
        )
        print(generated.to_response())
    if generated.Status == Status.GENERATED:
        print_term_image(generated.image.tmp_path)


# @cli.command()
# def pdf2img(pdf: Annotated[Path, typer.Argument()]):
#     img = to_pil(pdf)
#     print(get_term_image(image=img, height=40))


# @cli.command()
# def add_company(name: str):
#     company, created = Company.get_or_create(name=name)
#     logging.debug(f"Created: {created}")
#     logging.info(f"\n{company.to_table()}")


# @cli.command()
# def add_cv(cv_path: Annotated[Path, typer.Argument()]):
#     cv = CV.from_path(cv_path)
#     logging.info(f"\n{cv.to_table()}")


# @cli.command()
# def add_location(country: str, city: str):
#     location, created = Location.get_or_create(country_iso=to_iso(country), city=city)
#     logging.debug(f"Created: {created}")
#     logging.info(f"\n{location.to_table()}")


# @cli.command()
# def apply():
#     with apply_job_form() as form:
#         ans = form.ask()
#         input = ApplyInput(**ans)
#         logging.debug(input)
#         cmd_apply(input)


@cli.command()
def quit():
    raise typer.Exit()


# @cli.command()
# def job():
#     with select_job_form() as form:
#         ans = form.ask()
#         input = JobInput(**ans)
#         job: Job = Job.get(Job.slug == input.job_id)
#         rich.print(job.to_response())


@cli.callback()
def main(ctx: typer.Context):
    pass
