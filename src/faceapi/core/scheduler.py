import logging
from typing import Optional
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from urllib.parse import urlparse, parse_qs


class RedisNotConfiguredException(Exception):
    pass


class SchedulerMeta(type):
    _instance: Optional['Scheduler'] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    def start(cls):
        assert cls._instance
        logging.info(">> SCHEDULER start")
        cls._instance._scheduler.start()
    
    @property
    def is_running(cls) -> bool:
        return cls._instance._scheduler.running

    def stop(cls):
        try:
            assert cls._instance
            cls._instance._scheduler.shutdown()
        except Exception:
            pass

    def add_job(cls, *args, **kwargs):
        assert cls._instance
        return cls._instance._scheduler.add_job(*args, **kwargs)

    def get_job(cls, id, jobstore=None):
        assert cls._instance
        return cls._instance._scheduler.get_job(id, jobstore)

    def cancel_jobs(cls, id, jobstore=None):
        assert cls._instance
        return cls._instance._scheduler.remove_job(id, jobstore)

    def remove_all_jobs(cls, jobstore=None):
        assert cls._instance
        return cls._instance._scheduler.remove_all_jobs(jobstore)

    def get_jobs(cls, jobstore=None, pending=None):
        assert cls._instance
        return cls._instance._scheduler.get_jobs(jobstore, pending)


class Scheduler(object, metaclass=SchedulerMeta):

    _scheduler: BackgroundScheduler

    def __init__(self, scheduler: BackgroundScheduler, url: str) -> None:
        self._scheduler = scheduler
        redis_url = urlparse(url)
        redis_url_options = parse_qs(redis_url.query)
        jobstores = None

        if redis_url.scheme == "redis":
            jobstores = {
                "default": RedisJobStore(
                    host=redis_url.hostname,
                    db=int(redis_url.path.strip("/")),
                )
            }
        elif redis_url.scheme == "unix":
            jobstores = {
                "default": RedisJobStore(
                    unix_socket_path=redis_url.path,
                    db=int(redis_url_options.get("db", [])[0]),
                )
            }
        else:
            raise RedisNotConfiguredException("not valid REDIS_URL")
        self._scheduler.configure(jobstores=jobstores)
