from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from utils.document_loader import add_document_to_supabase_bytes
from utils.llm_answer import generate_answer_with_gemini
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "documents"  # private bucket

@app.route("/")
def home():
    return jsonify({"status": "running", "message": "LLM Query-Retrieval Backend"})

@app.route("/upload", methods=["POST"])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    file_name = file.filename
    file_bytes = file.read()

    # Check file size (limit 5 MB)
    if len(file_bytes) > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5 MB limit"}), 400

    # Upload file to Supabase Storage bucket (private)
    upload_res = supabase.storage.from_(BUCKET_NAME).upload(file_name, file_bytes)
    if upload_res and upload_res.get("error"):
        return jsonify({"error": upload_res["error"]["message"]}), 500

    # Generate a signed URL for the file (valid for 1 hour)
    signed_url_res = supabase.storage.from_(BUCKET_NAME).create_signed_url(file_name, 3600)
    signed_url = signed_url_res.get("signedURL") if signed_url_res else None

    try:
        # Ingest file into Supabase Vector directly from bytes
        res_ingest = add_document_to_supabase_bytes(file_bytes, file_name)
        return jsonify({
            "message": "Document uploaded successfully",
            "chunks": res_ingest["chunks"],
            "file_signed_url": signed_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    query_text = data.get("query")
    top_k = data.get("top_k", 3)

    if not query_text:
        return jsonify({"error": "No query provided"}), 400

    try:
        res = generate_answer_with_gemini(query_text, top_k=top_k)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
