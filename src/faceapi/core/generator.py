import logging
import time
from corestring import file_hash
from faceapi.database.database import Database
from faceapi.database.enums import ImageType, Status
from faceapi.database import Generated, Image, Prompt
from faceapi.masha.face2img import Face2Img
from queue import Empty, Queue
from corethread import StoppableThread


class Generator(StoppableThread):

    def __init__(self, queue: Queue, *args, **kwargs):
        self.queue = queue
        super().__init__(*args, **kwargs)

    def run(self):
        while not self.stopped():
            try:
                _, payload = self.queue.get()
                self.__generate(slug=payload)
                self.queue.task_done()
            except Empty:
                time.sleep(1)

    def __generate(self, slug: str):
        try:
            item: Generated = (
                Generated.select(Generated)
                .where((Generated.slug == slug) & (Generated.deleted == False))
                .get()
            )
            with Database.db.atomic():
                item.Status = Status.IN_PROGRESS
                item.save(only=["Status"])
            prompt: Prompt = item.prompt
            client = Face2Img(
                img_path=item.source.tmp_path,
                template=prompt.template,
                model=prompt.model,
                prompt=prompt.prompt,
                num_inference_steps=prompt.num_inference_steps,
                guidance_scale=prompt.guidance_scale,
                scale=prompt.scale,
                clip_skip=prompt.clip_skip,
                width=prompt.width,
                height=prompt.height,
                strength=prompt.strength,
                seed=int(prompt.seed),
                negative_prompt=prompt.negative_prompt
            )
            result_path, result_prompt = client.result()
            assert result_path
            if result_prompt:
                new_prompt, _ = Prompt.parse_prompt(result_prompt)
                item.prompt = new_prompt
            img, _ = Image.get_or_create(
                Type=ImageType.GENERATED,
                Image=result_path.as_posix(),
                hash=file_hash(result_path),
            )
            with Database.db.atomic():
                item.image = img
                item.Status = Status.GENERATED
                return item.save(only=["image", "Status", "prompt"])
        except Exception as e:
            logging.error(str(e))
            with Database.db.atomic():
                item.error = str(e)
                item.Status = Status.ERROR
                return item.save(only=["error", "Status"])
