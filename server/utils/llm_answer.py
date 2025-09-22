# import os
# import google.generativeai as genai
# from utils.retriever import query_documents
# # from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_THINKING_BUDGET
# from dotenv import load_dotenv

# load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# GEMINI_MODEL = os.getenv("GEMINI_MODEL")
# GEMINI_THINKING_BUDGET = int(os.getenv("GEMINI_THINKING_BUDGET"))  # 0 = disabled thinking

# # Configure the client
# genai.configure(api_key=GEMINI_API_KEY)

# def generate_answer_with_gemini(query: str, top_k: int = 3):
#     """
#     Retrieve top_k chunks, then call Gemini 2.5 Flash API to generate answer
#     """
#     # Step 1: retrieve
#     results = query_documents(query, top_k=top_k)
#     context = "\n\n".join([r['content'] for r in results])

#     # Step 2: build prompt
#     prompt = f"""You are an AI assistant. Use the context below to answer the question.
# If the answer is not in the context, respond honestly that you don't know.

# Context:
# {context}

# Question:
# {query}

# Answer with references:
# """

#     # Step 3: Call Gemini API
#     # Using the client library's generate_content method
#     # The docs show specifying a "contents" list
#     # and optionally a thinking_config if available. :contentReference[oaicite:2]{index=2}

#     # Build contents according to Gemini API schema
#     contents = [
#         {
#             "parts": [
#                 { "text": prompt }
#             ]
#         }
#     ]

#     # Build config
#     config = {}
#     # If thinking budget is > 0, include thinking_config
#     if GEMINI_THINKING_BUDGET > 0:
#         # Using docs: generate_content(config=types.GenerateContentConfig(thinking_config=...)) :contentReference[oaicite:3]{index=3}
#         from google.genai import types
#         config = {
#             "thinking_config": types.ThinkingConfig(thinking_budget=GEMINI_THINKING_BUDGET)
#         }

#     # Make the API call
#     response = genai.client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=contents,
#         config=config if config else None
#     )

#     # Extract answer
#     # The response.text is usually in response.candidates[0].text or equivalent
#     # Depending on API version
#     answer = response.text if hasattr(response, "text") else None
#     if not answer:
#         # fallback: sometimes response.candidates…
#         if hasattr(response, "candidates") and len(response.candidates) > 0:
#             answer = response.candidates[0].content.parts[0].text  # check schema
#         else:
#             answer = ""

#     # Step 4: references
#     references = [r['metadata'] for r in results]

#     return {"answer": answer, "references": references}
import os
import google.generativeai as genai
import markdown2
from markupsafe import Markup
from utils.retriever import query_documents
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_THINKING_BUDGET = int(os.getenv("GEMINI_THINKING_BUDGET", "0"))  # default 0

# Configure the client
genai.configure(api_key=GEMINI_API_KEY)

def format_answer(raw_text: str) -> str:
    """
    Convert Gemini's markdown-ish text to styled HTML.
    """
    # Convert markdown to HTML
    html = markdown2.markdown(raw_text)
    # Wrap in Markup to mark safe for Flask
    return Markup(html)

def generate_answer_with_gemini(query: str, top_k: int = 3):
    """
    Retrieve top_k chunks, then call Gemini 2.5 Flash API to generate answer
    """
    # Step 1: retrieve
    results = query_documents(query, top_k=top_k)
    context = "\n\n".join([r['content'] for r in results])

    # Step 2: build prompt
    prompt = f"""You are an AI assistant. Use the context below to answer the question.
If the answer is not in the context, respond honestly that you don't know.

Context:
{context}

Question:
{query}

Answer with references:

Answer in clean Markdown with:
- bold dates
- each mitigation measure as a separate bullet line
- paragraphs separated by blank lines
"""

    contents = prompt  # simpler: just pass prompt text

    # Step 3: Call Gemini API
    model = genai.GenerativeModel(GEMINI_MODEL)

    # If thinking budget needed, supply via generation_config or safety_settings
    if GEMINI_THINKING_BUDGET > 0:
        response = model.generate_content(
            contents,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 512,
                # thinking budget is currently preview feature; 
                # can be added if SDK supports it:
                # "thinking_budget": GEMINI_THINKING_BUDGET
            }
        )
    else:
        response = model.generate_content(contents)

    answer = response.text
    answer_html = format_answer(answer)

    # references = [r['metadata'] for r in results]
    references = []
    for r in results:
        # e.g. if your retriever returns: {'metadata': {'doc_name': 'file1.pdf'}}
        # you can adjust depending on how you store metadata
        references.append(r['metadata'])

    return {"answer": answer_html, "references": references}
