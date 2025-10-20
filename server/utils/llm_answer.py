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
    html = markdown2.markdown(raw_text)
    # Wrap in Markup to mark safe for Flask
    return Markup(html)

def generate_answer_with_gemini(query: str, user_id: str, top_k: int = 3):
    """
    Retrieve top_k chunks, then call Gemini 2.5 Flash API to generate answer
    """
    # Step 1: retrieve
    results = query_documents(query, user_id=user_id, top_k=top_k)
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
- Bold important terms
- Bullet points where suitable
- Separate paragraphs with blank lines
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

    # Step 4: Format answer
    answer = response.text
    answer_html = format_answer(answer)

    references = []
    for r in results:        
        references.append(r['metadata'])

    return {"answer": answer_html, "references": references}
