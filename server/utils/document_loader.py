import io, os, uuid
from typing import List
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
    )
    return splitter.split_text(text)


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


def add_document_to_supabase_bytes(file_bytes: bytes, file_name: str, user_id: str, file_url: str = None):
    
    clean_name = os.path.basename(file_name)
    
    text = process_file_bytes(file_bytes, file_name)
    chunks = chunk_text(text)
    embeddings = model.encode(chunks).tolist()

    for i, chunk in enumerate(chunks):
        metadata = {"source": clean_name, "chunk_id": str(uuid.uuid4()), "user_id": user_id, "file_url": file_url}
        supabase.table("documents").insert({
            "user_id": user_id,
            "content": chunk,
            "metadata": metadata,
            "embedding": embeddings[i]
        }).execute()

    return {"status": "ok", "chunks": len(chunks)}
