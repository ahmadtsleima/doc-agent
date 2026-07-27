import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from search import search_chunks

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL")
async def ask_llm(question: str) -> str:
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(temperature=0.2)
    )
    return response.text



async def ask_llm_stream(question: str):
    stream = await client.aio.models.generate_content_stream(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(temperature=0.2)
    )
    async for chunk in stream:
        if chunk.text:
            yield chunk.text



async def answer_from_documents(question: str) -> str:
    
    rows = await search_chunks(question, top_k=3)

    # assemble the retrieved chunks into a context block
    context = "\n\n---\n\n".join(chunk.content for chunk, distance in rows)

    prompt = f"""You are a document assistant. Answer the question using ONLY the context below.
If the answer is not in the context, say exactly: "I couldn't find that in the document."
Do not use outside knowledge.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.1)
    )
    return response.text