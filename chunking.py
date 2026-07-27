def chunk_text(text:str, chunk_size:int=500, overlap:int=100) -> list[str]:
  """Split text into overlapping chunks.
    Chunk 1: characters 0–500
    Chunk 2: characters 400–900   (starts 100 back — the overlap)
    Chunk 3: characters 800–1300
    ...continue until the text is exhausted.
    """
  chunks= []
  start = 0
  while start <len(text):
    end = start + chunk_size
    chunk = text[start:end]
    chunks.append(chunk)
    start += chunk_size - overlap
  return chunks



if __name__ == "__main__":
    from pypdf import PdfReader
    reader = PdfReader("uploads/TOEFL_2026_Diagnostic_Test.pdf")
    text = "".join(page.extract_text() + "\n" for page in reader.pages)

    chunks = chunk_text(text)
    print(f"{len(chunks)} chunks")
    for i, c in enumerate(chunks):
        print(f"--- chunk {i} ({len(c)} chars) ---")
        print(c[:80])