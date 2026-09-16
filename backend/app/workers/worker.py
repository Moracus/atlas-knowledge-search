from arq.connections import RedisSettings
from app.workers.tasks import process_document
from app.core.logging import setup_logging
from app.core.config import settings
import logging
REDIS_SETTINGS = RedisSettings(
    host=settings.redis_host,
    port=6379,
)

async def startup(ctx):
    setup_logging()
    logging.getLogger(__name__).info("Worker logging initialized")

class WorkerSettings:
    functions = [process_document]
    redis_settings = REDIS_SETTINGS
    on_startup = startup