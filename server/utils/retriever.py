import os
from supabase import create_client
from utils.embeddings import embed_text
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def query_documents(query: str, user_id: str, top_k: int = 3):
    embedding = embed_text([query])[0]

    result = supabase.rpc("match_documents", {
        "query_embedding": embedding,
        "match_count": top_k,
        "filter_user_id": user_id
    }).execute()

    return result.data  # [{id, content, metadata, embedding, distance}, ...]

