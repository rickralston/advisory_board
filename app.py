from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import openai
import logging
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)

# OpenAI API Key (ensure this is set in your Render environment)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Persona definitions
personas = {
    "CMO": "You are a Chief Marketing Officer with expertise in go-to-market strategies, pricing models, and brand positioning.",
    "CTO": "You are a Chief Technology Officer experienced in technology feasibility, software development, and scaling infrastructure.",
    "CFO": "You are a Chief Financial Officer skilled in financial modeling, fundraising, and business projections.",
    "Legal Advisor": "You are a legal expert specializing in M&A transactions, startup legal structures, and compliance for fundraising.",
    "Business Analyst": "You are a business analyst focused on competitive research, market trends, and industry positioning.",
}

@app.route("/ask", methods=["POST"])
def ask_advisory_board():
    """Handles business idea submission and returns persona-based insights."""
    data = request.get_json()
    business_idea = data.get("idea", "").strip()

    if not business_idea:
        return jsonify({"error": "No business idea provided"}), 400

    responses = []
    for role, description in personas.items():
        prompt = f"{description}\n\nA startup founder submits this business idea:\n\n{business_idea}\n\nProvide your expert opinion, including key risks, opportunities, and a score from 1-10."
        
        try:
            ai_response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "system", "content": prompt}]
            )
            response_text = ai_response["choices"][0]["message"]["content"]
            score = extract_score(response_text)  # Function to extract 1-10 score
            
            responses.append({
                "persona": role,
                "response": response_text,
                "score": score
            })

            logging.info(f"{role} responded with score {score}: {response_text[:100]}...")

        except Exception as e:
            logging.error(f"Error generating response for {role}: {str(e)}")
            responses.append({"persona": role, "response": "Error generating response.", "score": None})

    return jsonify({"responses": responses})

def extract_score(text):
    """Extracts a 1-10 score from the AI response (simple heuristic)."""
    import re
    match = re.search(r"\b([1-9]|10)\b", text)
    return int(match.group(1)) if match else None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT not set
    app.run(host="0.0.0.0", port=port, debug=True)
