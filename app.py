import os
import logging
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import AsyncOpenAI

app = Flask(__name__)

CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set the OPENAI_API_KEY environment variable.")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Define AI personas
personas = {
    "CMO": "You are a Chief Marketing Officer. Provide insights on go-to-market strategy and pricing. Start your response with a score from 1 to 10, indicating the strength of the idea from a marketing perspective. Start your response with only the number (1-10), followed immediately by a single newline (\n). Do not include any extra spaces, words, or formatting before or after the number.",
    "CTO": "You are a Chief Technology Officer. Evaluate technical feasibility and development timelines. Start your response with a score from 1 to 10, indicating the technical feasibility. Start your response with only the number (1-10), followed immediately by a single newline (\n). Do not include any extra spaces, words, or formatting before or after the number.",
    "CFO": "You are a Chief Financial Officer. Analyze financial projections and funding requirements. Start your response with a score from 1 to 10, indicating financial viability. Start your response with only the number (1-10), followed immediately by a single newline (\n). Do not include any extra spaces, words, or formatting before or after the number.",
    "Legal Advisor": "You are a Legal Advisor. Assess legal considerations for fundraising and M&A. Start your response with a score from 1 to 10, indicating legal feasibility. Start your response with only the number (1-10), followed immediately by a single newline (\n). Do not include any extra spaces, words, or formatting before or after the number.",
    "Business Analyst": "You are a Business Analyst. Conduct market and competitive analysis. Start your response with a score from 1 to 10, indicating market potential. Start your response with only the number (1-10), followed immediately by a single newline (\n). Do not include any extra spaces, words, or formatting before or after the number."
}

@app.route("/ask", methods=["POST"])
async def ask():
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
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=300  # Limit response length
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error generating response for {role}: {str(e)}")
            return "Error generating response."
    
    responses = await asyncio.gather(*[get_response(role, prompt) for role, prompt in personas.items()])
    return jsonify(dict(zip(personas.keys(), responses)))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
