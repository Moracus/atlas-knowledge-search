import uuid
from app.db.database import SessionLocal
from app.db.models import Document,Job
from app.repositories.documents import get_job_by_id,get_document_by_id
import asyncio
async def process_document(ctx,job_id:str):
    db = SessionLocal()
    job_id = uuid.UUID(job_id)
    try:
        job:Job = get_job_by_id(db,job_id)
        if not job :
            return
        doc : Document= get_document_by_id(db,job.id)


        if not job or not doc:
            return
        job.status = "processing"
        doc.status = "processing"
        

        db.commit()
        await asyncio.sleep(5)
        job.status = "completed"
        doc.status = "ready"
        db.commit()
        db.refresh(job)
        db.refresh(doc)
    except Exception:
       db.rollback()
       if job:
          job.status="failed"
          doc.status="failed"
          db.commit()
          raise
    finally:
       db.close()

    print("process finsished")

