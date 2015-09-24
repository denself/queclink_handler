from .parser import Settings
import os
import sys


__all__ = ['settings',]

def rel(*x):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *x))

sys.path.insert(0, rel('..', 'apps'))

settings = Settings()
settings.BASE_DIR = rel('../')
settings.LOG_DIR = rel(settings.BASE_DIR, 'logs')
settings.REDIS_HOST = 'localhost'
settings.REDIS_PORT = 6379
settings.REDIS_DB = 0
settings.REDIS_CELERY_DB = 2

settings.CACHE = {
    'backend': 'tornado_commons.cache.backends.redis_pickled.MessagePackPickledRedisCache',
    'servers': [{
        'host': settings.REDIS_HOST,
        'port': settings.REDIS_PORT,
        'db': 1
    }]
}

from settings import settings
from hot_redis.types import HotClient as PatchedRedis
from durabledict import RedisDict
from commons import redis_keys

settings['redis_conn'] = redis_conn = PatchedRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    socket_timeout=60)
settings['celery_redis_conn'] = PatchedRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_CELERY_DB)

settings.SYNC_TABLE = RedisDict(redis_keys.SYNC_TABLE_KEY, redis_conn)
