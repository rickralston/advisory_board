import os
import logging
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import AsyncOpenAI, OpenAIError

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("Missing OpenAI API key. Exiting...")
    exit(1)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

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
                max_tokens=150 if "score" in prompt_intro.lower() else 300
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            logging.error(f"OpenAI API error for {role}: {str(e)}")
            return "API error occurred."
        except ValueError:
            logging.error(f"Value error parsing response for {role}.")
            return "Error parsing response."
        except Exception as e:
            logging.error(f"Unexpected error for {role}: {str(e)}")
            return "An unexpected error occurred."

    # Gather responses from all personas
    responses = await asyncio.gather(*[get_response(role, prompt) for role, prompt in personas.items()])
    response_dict = dict(zip(personas.keys(), responses))

    # Extract scores and calculate average safely
    scores = []
    for response in response_dict.values():
        try:
            score = int(response.strip().split("\n")[0])
            scores.append(score)
        except (ValueError, IndexError):
            logging.error(f"Invalid score format in response: {response}")
            scores.append(0)  # Default to 0 if invalid

    # Compute total score
    total_score = round(sum(scores) / len(scores), 1) if scores else "N/A"
    response_dict["Total Score"] = str(total_score)

    return jsonify(response_dict)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=True)
