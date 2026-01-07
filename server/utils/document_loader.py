import io, os, uuid
from typing import List
from supabase import create_client
from pypdf import PdfReader
import docx
import re
from utils.embeddings import embed_text
from utils.chunker import split_into_blocks
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[str]:

    blocks = split_into_blocks(text)
    chunks = []
    current = ""

    def push(chunk):
        if chunk:
            chunks.append(chunk.strip())

    for block in blocks:
        if len(block) > chunk_size:
            # Sentence split fallback
            sentences = re.split(r'(?<=[.!?])\s+', block)
            for sentence in sentences:
                if len(current) + len(sentence) <= chunk_size:
                    current += " " + sentence
                else:
                    push(current)
                    current = sentence
        else:
            if len(current) + len(block) <= chunk_size:
                current += "\n" + block
            else:
                push(current)
                current = block

    push(current)

    # Overlap handling
    final = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            final.append(chunk)
        else:
            overlap_text = chunks[i-1][-overlap:]
            final.append(overlap_text + " " + chunk)

    return final


def process_file_bytes(file_bytes: bytes, file_name: str) -> str:
    ext = os.path.splitext(file_name)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        return "".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        return file_bytes.decode("utf-8")

def add_document_to_supabase_bytes(
    file_bytes: bytes,
    file_name: str,
    user_id: str,
    file_url: str = None
):
    text = process_file_bytes(file_bytes, file_name)
    chunks = chunk_text(text)

    embeddings = embed_text(chunks)

    for chunk, embedding in zip(chunks, embeddings):
        # print("Embedding length:", len(embedding))
        supabase.table("documents").insert({
            "user_id": user_id,
            "content": chunk,
            "metadata": {
                "source": file_name,
                "user_id": user_id,
                "file_url": file_url,
                "chunk_id": str(uuid.uuid4())
            },
            "embedding": embedding
        }).execute()

    return {"status": "ok", "chunks": len(chunks)}
