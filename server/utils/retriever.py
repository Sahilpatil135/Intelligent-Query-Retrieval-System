import os
import numpy as np
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase + Model
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def query_documents(query: str, user_id: str, top_k: int = 3):
    embedding = model.encode([query])[0].tolist()

    # Call the match_documents function
    result = supabase.rpc("match_documents", {
        "query_embedding": embedding,
        "match_count": top_k,
        "filter_user_id": user_id  
    }).execute()

    return result.data  # [{id, content, metadata, embedding, distance}, ...]

# if __name__ == "__main__":
#     # q = "Define vulnerability?"
#     q = "Explain briefly the pattern of global population growth in recent times?"
#     results = query_documents(q, top_k=3)
#     print(f"\n🔎 Query: {q}\n")
#     for i, res in enumerate(results, start=1):
#         print(f"Result {i}:")
#         print(f"  Text     : {res['content'][:200]}...")
#         print(f"  Source   : {res['metadata'].get('source', 'N/A')}")
#         print(f"  Similarity : {res['distance']}\n")
