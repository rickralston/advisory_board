import os
import asyncio
import logging
import bcrypt
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from openai import AsyncOpenAI
from datetime import timedelta

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_default_secret_key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
jwt = JWTManager(app)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define AI personas
personas = {
    "CMO": "You are a Chief Marketing Officer. Provide insights on go-to-market strategy and pricing. Start your response with a score from 1 through 10, indicating the strength of the idea from a marketing perspective. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "CTO": "You are a Chief Technology Officer. Evaluate technical feasibility and development timelines. Start your response with a score from 1 through 10, indicating the technical feasibility. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "CFO": "You are a Chief Financial Officer. Analyze financial projections and funding requirements. Start your response with a score from 1 through 10, indicating financial viability. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "Legal Advisor": "You are a Legal Advisor. Assess legal considerations for fundraising and M&A. Start your response with a score from 1 through 10, indicating legal feasibility. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "Business Analyst": "You are a Business Analyst. Conduct market and competitive analysis. Start your response with a score from 1 through 10, indicating market potential. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number."
}

async def get_response(role, prompt):
    """Asynchronously fetch responses from OpenAI."""
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": role}
            ],
            max_tokens=300
        )
        return {"role": role, "response": response.choices[0].message.content.strip()}
    except Exception as e:
        logging.error(f"Error fetching response for {role}: {e}")
        return {"role": role, "response": "Error generating response."}

@app.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    username = request.json.get("username")
    password = request.json.get("password")
    if username == "test" and password == "password":
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/ask', methods=['POST'])
@jwt_required()
async def ask():
    """Handle user questions and get responses from AI advisors."""
    data = request.json
    idea = data.get("idea", "")
    logging.info(f"Received business idea: {idea}")
    
    if not idea:
        return jsonify({"error": "No business idea provided."}), 400
    
    responses = await asyncio.gather(*[get_response(role, f"{prompt}\n\nBusiness Idea: {idea}") for role, prompt in personas.items()])
    return jsonify(responses), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 10000))  # Use Render's dynamic port
    app.run(host='0.0.0.0', port=port)
