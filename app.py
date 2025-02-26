import os
import logging
import asyncio
import supabase
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import AsyncOpenAI

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not OPENAI_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing environment variables. Set OPENAI_API_KEY, SUPABASE_URL, and SUPABASE_KEY.")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Connect to Supabase
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# Define AI personas
personas = {
    "CMO": "You are a Chief Marketing Officer. Provide insights on go-to-market strategy and pricing. Start your response with a score from 1 through 10, indicating the strength of the idea from a marketing perspective. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "CTO": "You are a Chief Technology Officer. Evaluate technical feasibility and development timelines. Start your response with a score from 1 through 10, indicating the technical feasibility. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "CFO": "You are a Chief Financial Officer. Analyze financial projections and funding requirements. Start your response with a score from 1 through 10, indicating financial viability. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "Legal Advisor": "You are a Legal Advisor. Assess legal considerations for fundraising and M&A. Start your response with a score from 1 through 10, indicating legal feasibility. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number.",
    "Business Analyst": "You are a Business Analyst. Conduct market and competitive analysis. Start your response with a score from 1 through 10, indicating market potential. Start your response with only the number 1 through 10, followed immediately by a single newline (\n). Do not include any extra spaces, words, multiple newlines, or formatting before or after the number."
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

    # Gather responses from all personas
    responses = await asyncio.gather(*[get_response(role, prompt) for role, prompt in personas.items()])
    response_dict = dict(zip(personas.keys(), responses))

    # Extract scores and calculate average
    try:
        scores = [int(response.split("\n")[0]) for response in response_dict.values()]
        total_score = round(sum(scores) / len(scores), 1)  # Average with one decimal place
    except Exception as e:
        logging.error(f"Error calculating total score: {str(e)}")
        total_score = "N/A"

    # Add total score to response
    response_dict["Total Score"] = str(total_score)

    return jsonify(response_dict)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
