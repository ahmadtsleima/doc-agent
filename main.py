from fastapi import FastAPI
from sqlalchemy import select
from database import SessionLocal
from models import Document, DocumentCreate
from fastapi import UploadFile, File
from pathlib import Path
import uuid
from pydantic import BaseModel
from llm import ask_llm,ask_llm_stream
from fastapi.responses import StreamingResponse
from ingest import ingest_document
from llm import answer_from_documents

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/health")
async  def health_check():
    return {"status": "ok"}

@app.get("/echo/{message}")
async def echo(message: str):
    return {"message": message}

@app.post("/documents")
async def creat_document(data : DocumentCreate):
    async with SessionLocal() as session:
        doc = Document(filename=data.filename)
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return {"id": doc.id, "filename": doc.filename}

@app.get("/documents")
async def list_documents():
    async with SessionLocal() as session:
        result = await session.execute(select(Document))
        docs = result.scalars().all()
        return [{"id": d.id, "filename": d.filename} for d in docs]
    
@app.post("/upload")
async def upload_document(file: UploadFile):
    contents = await file.read()
    stored_name = f"{uuid.uuid4()}.pdf"
    stored_path = str(UPLOAD_DIR / stored_name) 
    (UPLOAD_DIR / stored_name).write_bytes(contents)
    async with SessionLocal() as session:
        doc = Document(filename=file.filename, stored_path=stored_path)
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        doc_id = doc.id
    await ingest_document(doc_id, stored_path)
    return {"id": doc_id, "filename": file.filename, "status": "uploaded and ingested"}
    
class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(request: AskRequest):
    answer = await ask_llm(request.question)
    return {"question": request.question, "answer": answer}


@app.post("/ask-stream")
async def ask_stream(request: AskRequest):
    return StreamingResponse(
        ask_llm_stream(request.question), 
        media_type="text/plain"
        )


@app.post("/ask-document")
async def ask_document(request: AskRequest):
    answer = await answer_from_documents(request.question)
    return {"question": request.question, "answer": answer}