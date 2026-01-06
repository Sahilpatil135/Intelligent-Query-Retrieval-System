import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def embed_text(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using Gemini (FREE)
    """
    response = genai.embed_content(
        model="models/text-embedding-004",
        content=texts
    )
    return response["embedding"]
