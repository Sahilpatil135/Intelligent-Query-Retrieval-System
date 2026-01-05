from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from utils.document_loader import add_document_to_supabase_bytes
from utils.llm_answer import generate_answer_with_gemini
import os
import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)    

BUCKET_NAME = "documents"  # private bucket


# ---------------------- VERIFY USER ----------------------
def verify_user(request):
    """Verify Supabase user using the JWT token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, "Missing or invalid Authorization header"

    token = auth_header.split(" ")[1]

    try:
        # Try legacy JWT secret first (most reliable for Supabase)
        legacy_jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if legacy_jwt_secret:
            try:
                # Try with audience validation first
                payload = jwt.decode(token, legacy_jwt_secret, algorithms=["HS256"], audience="authenticated")
                return payload, None
            except jwt.InvalidAudienceError:
                # Try without audience validation
                try:
                    payload = jwt.decode(token, legacy_jwt_secret, algorithms=["HS256"], audience=None)
                    return payload, None
                except Exception as legacy_error:
                    print("Legacy JWT verification failed:", legacy_error)
            except Exception as legacy_error:
                print("Legacy JWT verification failed:", legacy_error)
        
        # Fallback: Try JWKS verification (modern approach)
        try:
            jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
            jwks = requests.get(jwks_url, timeout=10).json()

            if not jwks.get("keys"):
                raise Exception("No JWKS keys available")

            unverified_header = jwt.get_unverified_header(token)
            key = next((k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]), None)
            if not key:
                raise Exception("Invalid token key")

            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
            # Try with audience validation first
            try:
                payload = jwt.decode(token, public_key, algorithms=["RS256"], audience="authenticated")
                return payload, None
            except jwt.InvalidAudienceError:
                # Try without audience validation
                payload = jwt.decode(token, public_key, algorithms=["RS256"], audience=None)
                return payload, None
        except Exception as jwks_error:
            print("JWKS verification failed:", jwks_error)
            raise jwks_error
            
    except Exception as e:
        print("Token verification failed:", e)
        return None, str(e)


# ---------------------- ROUTES ----------------------
@app.route("/")
def home():
    return jsonify({"status": "running", "message": "LLM Query-Retrieval Backend"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/upload", methods=["POST"])
def upload_document():
    
    # 1. Verify user
    user, error = verify_user(request)
    if error:
        return jsonify({"error": "Unauthorized", "details": error}), 401

    user_id = user["sub"]  # Supabase user UUID
    print("Uploading for user:", user_id)
    
    # 2. Check for file
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    file_name = file.filename
    file_bytes = file.read()

    # 3. Check file size (limit 5 MB)
    if len(file_bytes) > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5 MB limit"}), 400

    # 4️. Use per-user storage path
    path = f"{user_id}/{file_name}"

    # 5. Upload file to Supabase Storage bucket (private)
    upload_res = supabase.storage.from_(BUCKET_NAME).upload(file_name, file_bytes)

    if hasattr(upload_res, "error") and upload_res.error:
        return jsonify({"error": upload_res.error.get("message", "Upload failed")}), 500
    
    # 6. Generate a signed URL for the file (valid for 1 hour)
    signed_url_res = supabase.storage.from_(BUCKET_NAME).create_signed_url(file_name, 3600)
    signed_url = signed_url_res.get("signedURL") if isinstance(signed_url_res, dict) else None

    # 7️. Add to Supabase Vector (tagged with user_id)
    try:
        # Ingest file into Supabase Vector directly from bytes
        res_ingest = add_document_to_supabase_bytes(file_bytes, path, user_id=user_id, file_url=signed_url)
        return jsonify({
            "message": "Document uploaded successfully",
            "user_id": user_id,
            "chunks": res_ingest.get("chunks", []),
            "file_signed_url": signed_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/query", methods=["POST"])
def query():
    print("Query endpoint called")
    print("Headers:", dict(request.headers))
    
    # 1. Verify user
    user, error = verify_user(request)
    if error:
        print("Authentication failed:", error)
        return jsonify({"error": "Unauthorized", "details": error}), 401
    user_id = user["sub"]  # Supabase user UUID
    print("Querying for user:", user_id)

    # 2. Get query and top_k from request
    data = request.get_json()
    query_text = data.get("query")
    top_k = data.get("top_k", 3)

    if not query_text:
        return jsonify({"error": "No query provided"}), 400

    # 3. Check if user has documents uploaded
    doc_res = supabase.table("documents").select("id").eq("user_id", user_id).limit(1).execute()
    if not doc_res.data or len(doc_res.data) == 0:
        return jsonify({
            "error": "No documents found.",
            "message": "You have not uploaded any documents yet. Please upload one first."
        }), 400

    # 4. Generate context-aware answer for this user only
    try:
        res = generate_answer_with_gemini(query_text, user_id=user_id, top_k=top_k)
        res["user_id"] = user_id
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
