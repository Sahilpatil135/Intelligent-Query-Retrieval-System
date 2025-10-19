# import os
# import uuid
# from typing import List
# from supabase import create_client, Client
# from sentence_transformers import SentenceTransformer
# from pypdf import PdfReader
# import docx
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from dotenv import load_dotenv

# load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# # Initialize Supabase client
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# # Embeddings model
# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# def load_pdf(file_path: str) -> str:
#     reader = PdfReader(file_path)
#     return "".join(page.extract_text() or "" for page in reader.pages)

# def load_docx(file_path: str) -> str:
#     doc = docx.Document(file_path)
#     return "\n".join(p.text for p in doc.paragraphs)

# def load_txt(file_path: str) -> str:
#     with open(file_path, "r", encoding="utf-8") as f:
#         return f.read()

# def load_document(file_path: str) -> str:
#     ext = os.path.splitext(file_path)[1].lower()
#     if ext == ".pdf": return load_pdf(file_path)
#     elif ext == ".docx": return load_docx(file_path)
#     elif ext == ".txt": return load_txt(file_path)
#     else: raise ValueError(f"Unsupported file type: {ext}")

# def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=overlap,
#         length_function=len,
#     )
#     return splitter.split_text(text)

# def file_already_uploaded(file_path: str) -> bool:
#     """
#     Check if a file is already uploaded to Supabase by metadata.source.
#     """
#     response = supabase.table("documents").select("id").contains("metadata", {"source": file_path}).execute()
#     return len(response.data) > 0

# def add_document_to_supabase(file_path: str):
#     if file_already_uploaded(file_path):
#         print(f"Skipping {file_path}: already uploaded")
#         return
    
#     text = load_document(file_path)
#     chunks = chunk_text(text)
#     embeddings = model.encode(chunks).tolist()

#     for i, chunk in enumerate(chunks):
#         metadata = {"source": file_path, "chunk_id": str(uuid.uuid4())}
#         supabase.table("documents").insert({
#             "content": chunk,
#             "metadata": metadata,
#             "embedding": embeddings[i]
#         }).execute()

#     print(f"{file_path} uploaded to Supabase Vector ({len(chunks)} chunks)")

# if __name__ == "__main__":
#     docs_folder = "../data"
#     for file in os.listdir(docs_folder):
#         path = os.path.join(docs_folder, file)
#         if os.path.isfile(path):
#             try:
#                 add_document_to_supabase(path)
#             except Exception as e:
#                 print(f"Skipping {file}: {e}")
# utils/document_loader.py
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
