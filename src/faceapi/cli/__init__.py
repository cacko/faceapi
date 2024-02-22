from pathlib import Path
from click import pass_context
from rich import print
import typer
from faceapi.core.commands import Command
from faceapi.database.enums import ImageType
from faceapi.main import serve
from faceapi.database import Generated, Image, Prompt, create_tables
from typing_extensions import Annotated
from coreimage.terminal import print_term_image
import logging
from corestring import file_hash
from faceapi.core.queue import GeneratorQueue

cli = typer.Typer()


@cli.command()
def serve_api():
    serve()


@cli.command()
def init_db():
    try:
        assert typer.confirm("Dropping all data?")
        create_tables(drop=True)
    except AssertionError:
        logging.info("ignored")


@cli.command()
def generate(
    face_path: Annotated[Path, typer.Argument()],
    template: Annotated[str, typer.Option("-t", "--template")] = None,
    model: Annotated[str, typer.Option("-m", "--model")] = None,
    prompt: Annotated[str, typer.Option("-p", "--prompt")] = None,
    num_inferance_steps: Annotated[
        int, typer.Option("-i", "--num_inferance_steps")
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
    print_term_image(image_path=face_path)
    generated, _ = Generated.get_or_create(
        model=model,
        template=template,
        prompt=prompt,
        uid="dev",
        source=source,
        num_inferance_steps=num_inferance_steps,
        guidance_scale=guidance_scale,
        scale=scale,
        clip_skip=clip_skip,
        width=width,
        height=height,
    )
    GeneratorQueue().put_nowait((Command.GENERATE, generated.slug))
    print_term_image(generated.image.tmp_path, height=30)
    print(generated.to_response())    


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
