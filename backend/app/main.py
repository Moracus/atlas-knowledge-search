from fastapi import FastAPI

from app.api.documents import router as documents_router

from app.core.redis import lifespan

app = FastAPI(title="Atlas API",lifespan=lifespan)

app.include_router(documents_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}