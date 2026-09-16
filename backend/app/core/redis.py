from contextlib import asynccontextmanager
import fastapi
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
redis_host = settings.redis_host

@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    app.state.redis = await create_pool(RedisSettings(host=redis_host,port=6379))

    yield

    await app.state.redis.aclose()

