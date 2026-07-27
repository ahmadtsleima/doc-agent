import os
from pypdf import PdfReader
from google import genai
from dotenv import load_dotenv
from database import SessionLocal, engine
from models import Chunk
from chunking import chunk_text


load_dotenv()
client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# model_12 = os.getenv("GEMINI_MODEL")
async def ingest_document(document_id:int, pdf_path:str):
    reader = PdfReader(pdf_path)
    text = "".join(page.extract_text() + "\n" for page in reader.pages)


    chunks = chunk_text(text)
    print(f"split into {len(chunks)} chunks")

    async with SessionLocal() as session:
        for i, chunk_content in enumerate(chunks):
            result = client.aio.models.embed_content(
                model="gemini-embedding-001",
                contents=chunk_content
            )

            vector = result.embeddings[0].values
            chunk= Chunk(
                document_id=document_id,
                content=chunk_content,
                embedding=vector
            )
            session.add(chunk)
            print(f"embedded chunk + staged chunk {i}")

        await session.commit()
    print("Done - all chunks stored")