import os
import logging
import asyncio
import openai
from flask import Flask, request, jsonify
from openai import AsyncOpenAI

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set the OPENAI_API_KEY environment variable.")

# Initialize OpenAI async client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Define AI personas
personas = {
    "CMO": "You are a Chief Marketing Officer. Provide insights on go-to-market strategy and pricing.",
    "CTO": "You are a Chief Technology Officer. Evaluate technical feasibility and development timelines.",
    "CFO": "You are a Chief Financial Officer. Analyze financial projections and funding requirements.",
    "Legal Advisor": "You are a Legal Advisor. Assess legal considerations for fundraising and M&A.",
    "Business Analyst": "You are a Business Analyst. Conduct market and competitive analysis."
}

async def generate_response(role, prompt_intro, business_idea):
    """Generate response from OpenAI asynchronously."""
    messages = [
        {"role": "system", "content": prompt_intro},
        {"role": "user", "content": f"Business Idea: {business_idea}. What are your thoughts?"}
    ]
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # Change model as needed
            messages=messages
        )
        return role, response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating response for {role}: {str(e)}")
        return role, "Error generating response."

@app.route("/ask", methods=["POST"])
async def ask():
    data = request.get_json()
    if not data or "business_idea" not in data:
        return jsonify({"error": "No business idea provided"}), 400
    
    business_idea = data["business_idea"]
    logging.info(f"Received business idea: {business_idea}")
    
    # Run all persona requests concurrently
    tasks = [generate_response(role, prompt, business_idea) for role, prompt in personas.items()]
    responses = await asyncio.gather(*tasks)
    
    return jsonify(dict(responses))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
