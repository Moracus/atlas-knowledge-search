from fastapi import FastAPI

from app.api.documents import router as documents_router

app = FastAPI(title="Atlas API")

app.include_router(documents_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}