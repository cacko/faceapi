import boto3
from pathlib import Path
from faceapi.config import app_config
from corefile import TempPath
import filetype
import logging


class S3Meta(type):
    def __call__(cls, *args, **kwds):
        return type.__call__(cls, *args, **kwds)

    def upload(cls, src: Path, dst: str, skip_upload: bool = False) -> str:
        logging.debug(f"upload {src} to {dst}")
        return cls().upload_file(src, dst, skip_upload)
    
    def download(cls, key: str) -> Path:
        return cls().download_file(cls.src_key(key))

    def delete(cls, key: str):
        return cls().delete_file(cls.src_key(key))

    def src_key(cls, dst):
        return f"{app_config.aws.media_location}/{dst}"


class S3(object, metaclass=S3Meta):

    def __init__(self) -> None:
        cfg = app_config.aws
        logging.debug(cfg)
        self._client = boto3.client(
            service_name="s3",
            aws_access_key_id=cfg.access_key_id,
            aws_secret_access_key=cfg.secret_access_key,
            region_name=cfg.s3_region,
        )

    def upload_file(self, src: Path, dst, skip_upload=False) -> str:
        mime = filetype.guess_mime(src)
        key = self.__class__.src_key(dst)
        if not skip_upload:
            bucket = app_config.aws.storage_bucket_name
            res = self._client.upload_file(
                src,
                bucket,
                key,
                ExtraArgs={"ContentType": mime, "ACL": "public-read"},
            )
            logging.warning(res)
        return key

    def download_file(self, key: str, dst: Path = None) -> Path:
        if dst is None:
            pth = Path(key)
            dst = TempPath(pth.name)
        bucket = app_config.aws.storage_bucket_name
        res = self._client.download_file(
            Bucket=bucket,
            Key=key,
            Filename=dst.as_posix()
        )
        logging.warning(res)
        return dst

    def delete_file(self, file_name: str) -> bool:
        bucket = app_config.aws.storage_bucket_name
        return self._client.delete_object(Bucket=bucket, Key=file_name)
