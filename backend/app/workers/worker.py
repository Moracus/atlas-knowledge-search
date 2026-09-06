import asyncio
from arq import create_pool
from arq.connections import RedisSettings
from app.workers.tasks import process_document



REDIS_SETTINGS=RedisSettings(host='localhost',port=6379)


class WorkerSettings:
    functions = [process_document]
    redis_settings = REDIS_SETTINGS