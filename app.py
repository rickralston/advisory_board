import os
import logging
import asyncio
import supabase
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import AsyncOpenAI
from functools import wraps
import jwt
from datetime import datetime, timedelta
from flask_cors import cross_origin

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load API keys and Supabase credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")  # Used for signing authentication tokens

if not OPENAI_API_KEY or not SUPABASE_URL or not SUPABASE_KEY or not JWT_SECRET:
    raise ValueError("Missing environment variables. Ensure OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY, and JWT_SECRET are set.")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Connect to Supabase
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

def token_required(f):
    """Decorator to verify JWT token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            token = token.split("Bearer ")[-1]  # Extract token
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            request.user = decoded  # Store user info in request
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ✅ NEW: Simple Login Route to Generate JWT Token
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # 🔹 Temporary Hardcoded Credentials (Replace with Database Check Later)
    if username == "admin" and password == "password123":
        token = jwt.encode(
            {"user": username, "exp": datetime.utcnow() + timedelta(hours=1)},
            JWT_SECRET,
            algorithm="HS256"
        )
        return jsonify({"token": token})

    return jsonify({"error": "Invalid credentials"}), 401

# Define AI personas
personas = {
    "CMO": "You are a Chief Marketing Officer. Provide insights on go-to-market strategy and pricing. Start your response with a score from 1 through 10, indicating the strength of the idea from a marketing perspective. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "CTO": "You are a Chief Technology Officer. Evaluate technical feasibility and development timelines. Start your response with a score from 1 through 10, indicating the technical feasibility. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "CFO": "You are a Chief Financial Officer. Analyze financial projections and funding requirements. Start your response with a score from 1 through 10, indicating financial viability. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "Legal Advisor": "You are a Legal Advisor. Assess legal considerations for fundraising and M&A. Start your response with a score from 1 through 10, indicating legal feasibility. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "Business Analyst": "You are a Business Analyst. Conduct market and competitive analysis. Start your response with a score from 1 through 10, indicating market potential. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number."
}

@app.route("/ask", methods=["POST", "OPTIONS"])
@cross_origin()  # Allow frontend to make requests
@token_required  # Require authentication
def ask():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    data = request.get_json()
    if not data or "business_idea" not in data:
        return jsonify({"error": "No business idea provided"}), 400

    business_idea = data["business_idea"]
    logging.info(f"Received business idea: {business_idea}")

    async def get_response(role, prompt_intro):
        messages = [
            {"role": "system", "content": prompt_intro},
            {"role": "user", "content": f"Business Idea: {business_idea}. What are your thoughts? Keep your response concise."}
        ]
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error generating response for {role}: {str(e)}")
            return "Error generating response."

    # Run async functions synchronously
    responses = asyncio.run(asyncio.gather(*[get_response(role, prompt) for role, prompt in personas.items()]))
    response_dict = dict(zip(personas.keys(), responses))

    # Extract scores and calculate total
    try:
        scores = [int(response.split("\n")[0]) for response in response_dict.values()]
        total_score = round(sum(scores) / len(scores), 1)
    except Exception as e:
        logging.error(f"Error calculating total score: {str(e)}")
        total_score = "N/A"

    response_dict["Total Score"] = str(total_score)
    
    return jsonify(response_dict)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
