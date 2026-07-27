import os
from dotenv import load_dotenv
from google import genai
from sqlalchemy import select
from database import SessionLocal
from models import Chunk

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def search_chunks(question: str, top_k: int = 3):
    # 1. embed the question — SAME model, same space as the chunks
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question
    )
    question_vector = result.embeddings[0].values

    # 2. ask Postgres for the top_k nearest chunks by cosine distance
    async with SessionLocal() as session:
        stmt = (
            select(Chunk, Chunk.embedding.cosine_distance(question_vector).label("distance"))
            .order_by("distance")
            .limit(top_k)
        )
        results = await session.execute(stmt)
        return results.all()
