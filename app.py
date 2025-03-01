import os
import logging
import asyncio
import supabase
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from openai import AsyncOpenAI
from functools import wraps
import jwt
import re
from datetime import datetime, timedelta

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
        if not token or not token.startswith("Bearer "):
            return jsonify({"error": "Token is missing or invalid"}), 401
        
        try:
            token = token.split("Bearer ")[-1]  # Extract token
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            g.user = decoded  # Store user info globally
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Define AI personas
personas = {
    "CMO": "You are a Chief Marketing Officer. Provide insights on go-to-market strategy and pricing.",
    "CTO": "You are a Chief Technology Officer. Evaluate technical feasibility and development timelines.",
    "CFO": "You are a Chief Financial Officer. Analyze financial projections and funding requirements.",
    "Legal Advisor": "You are a Legal Advisor. Assess legal considerations for fundraising and M&A.",
    "Business Analyst": "You are a Business Analyst. Conduct market and competitive analysis."
}

@app.route("/ask", methods=["POST"])
@token_required  # Require authentication
async def ask():
    data = request.get_json()
    if not data or "business_idea" not in data:
        return jsonify({"error": "No business idea provided"}), 400

    business_idea = data["business_idea"]
    logging.info(f"Received business idea: {business_idea}")

    async def get_response(role, prompt_intro):
        messages = [
            {"role": "system", "content": prompt_intro},
            {"role": "user", "content": f"Business Idea: {business_idea}. Provide a concise evaluation. "
                                        f"Start with a score from 1 to 10 on a new line."}
        ]
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=200  # More concise response
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error generating response for {role}: {str(e)}")
            return "Error generating response."

    # Gather responses from all personas
    responses = await asyncio.gather(*[get_response(role, prompt) for role, prompt in personas.items()])
    response_dict = dict(zip(personas.keys(), responses))

    # Extract scores using regex (handles malformed responses)
    def extract_score(response):
        match = re.match(r"^\s*(\d+)", response)  # Find leading number
        return int(match.group(1)) if match else None

    scores = [extract_score(response) for response in response_dict.values()]
    valid_scores = [score for score in scores if score is not None]

    total_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else "N/A"
    response_dict["Total Score"] = str(total_score)

    return jsonify(response_dict)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

