from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource
from pathlib import Path
from typing import Optional, Any, Type
from appdirs import user_config_dir
from faceapi import __name__
from os import environ
import yaml

USER_CONFIG_PATH = Path(user_config_dir(appname=__name__))
DEFAULT_CONFIG_FILE_PATH = USER_CONFIG_PATH / "settings.yaml"

config_file = Path(environ.get("FACE_CONFIG_FILE", DEFAULT_CONFIG_FILE_PATH.as_posix()))

try:
    assert config_file.parent.exists()
except AssertionError:
    config_file.parent.mkdir(parents=True)


try:
    assert config_file.exists()
except AssertionError:
    raise RuntimeError(f"No config file as {config_file}")


class DbConfig(BaseModel):
    url: str


class RedisConfig(BaseModel):
    url: str

class FirebaseConfig(BaseModel):
    admin_json: str
    db: str
    
class AccessConfig(BaseModel):
    nsfw: list[any]

class ApiConfig(BaseModel):
    host: str
    port: int
    assets: str
    workers: Optional[int] = Field(default=1)
    web_host: Optional[str] = Field(default="https://face-api.cacko.net")


class AWSConfig(BaseModel):
    cloudfront_host: str
    access_key_id: str
    secret_access_key: str
    s3_region: str
    storage_bucket_name: str
    media_location: str


class MashaConfig(BaseModel):
    host: str
    port: int


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    
    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        return super().get_field_value(field, field_name)
    
    def __call__(self):
        try:
            pth = config_file
            assert pth.exists()
            data = yaml.full_load(Path(pth).read_text())
            return data
        except AssertionError:
            return {}

class Settings(BaseSettings):
    db: DbConfig
    redis: RedisConfig
    api: ApiConfig
    aws: AWSConfig
    firebase: FirebaseConfig
    masha: MashaConfig
    access: AccessConfig

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            env_settings,
        )


    class Config:
        env_nested_delimiter = "__"


app_config = Settings()  # type: ignore
