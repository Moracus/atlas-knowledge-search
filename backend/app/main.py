from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

app = FastAPI(title="Atlas API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"database": result.scalar()}