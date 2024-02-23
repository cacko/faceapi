import logging
import time
from typing import Optional, Any

from corestring import file_hash
from faceapi.database.enums import ImageType, Status
from faceapi.database import Generated, Image
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
                _, payload = self.queue.get_nowait()
                self.__generate(slug=payload)
                self.queue.task_done()
            except Empty:
                time.sleep(0.2)
                
                
    def __generate(self, slug: str):
        item: Generated = Generated.select(Generated).where(Generated.slug == slug).get()
        item.Status = Status.IN_PROGRESS
        item.save(only=["Status"])
        try:
            client = Face2Img(
                img_path=item.source.tmp_path,
                template=item.template,
                model=item.model,
                prompt=item.prompt,
                num_inferance_steps=item.num_inferance_steps,
                guidance_scale=item.guidance_scale,
                scale=item.scale,
                clip_skip=item.clip_skip,
                width=item.width,
                height=item.height,
            )
            result_path, result_prompt = client.result()
            assert result_path
            if result_prompt:
                item.parse_prompt(result_prompt)
            img, _ = Image.get_or_create(
                Type=ImageType.GENERATED, Image=result_path.as_posix(), hash=file_hash(result_path)
            )
            item.image = img
            item.Status = Status.GENERATED
            return item.save(only=["image", "Status"])
        except Exception as e:
            logging.error(str(e))
            item.error = str(e)
            item.Status = Status.ERROR
            return item.save(only=["error", "Status"])