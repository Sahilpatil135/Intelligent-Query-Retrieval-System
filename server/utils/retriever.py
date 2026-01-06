# import os
# import numpy as np
# from supabase import create_client, Client
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv

# load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# # Initialize Supabase + Model
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# def query_documents(query: str, user_id: str, top_k: int = 3):
#     embedding = model.encode([query])[0].tolist()

#     # Call the match_documents function
#     result = supabase.rpc("match_documents", {
#         "query_embedding": embedding,
#         "match_count": top_k,
#         "filter_user_id": user_id  
#     }).execute()

#     return result.data  # [{id, content, metadata, embedding, distance}, ...]

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

    return result.data

