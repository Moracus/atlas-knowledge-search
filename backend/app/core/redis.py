from contextlib import asynccontextmanager
import fastapi
from arq import create_pool
from arq.connections import RedisSettings


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    app.state.redis = await create_pool(RedisSettings(host="localhost",port=6379))

    yield

    await app.state.redis.aclose()

