import os
import logging
from flask import Flask, request, jsonify
import openai

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("Missing OpenAI API Key!")
    raise ValueError("OpenAI API Key is required.")

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Flask app
app = Flask(__name__)

# Persona definitions
personas = {
    "CMO": "Chief Marketing Officer with expertise in go-to-market and pricing strategies.",
    "CTO": "Chief Technology Officer experienced in technology feasibility and product development timelines.",
    "CFO": "Chief Financial Officer specializing in financial modeling and projections.",
    "Legal Advisor": "Legal expert in M&A transactions and fundraising legal considerations.",
    "Business Analyst": "Analyst focusing on competitive and market analysis."
}

@app.route("/ask", methods=["POST"])
def ask_advisory_board():
    try:
        data = request.get_json()
        logging.info("Received request data: %s", data)
        
        business_idea = data.get("business_idea")
        if not business_idea:
            logging.error("No business idea provided.")
            return jsonify({"error": "No business idea provided"}), 400
        
        responses = []
        for persona, description in personas.items():
            try:
                prompt = (
                    f"You are a {description} Provide feedback on the following business idea: {business_idea}. "
                    "Give your perspective, identify key challenges, and rate its potential on a scale of 1-10."
                )
                
                response = openai_client.completions.create(
                    model="gpt-4o",  # Ensure the correct model name is used
                    prompt=prompt,
                    max_tokens=200
                )
                
                ai_response = response.choices[0].text.strip()
                rating = extract_rating(ai_response)
                responses.append({
                    "persona": persona,
                    "response": ai_response,
                    "score": rating
                })
                
            except Exception as e:
                logging.error("Error generating response for %s: %s", persona, str(e))
                responses.append({
                    "persona": persona,
                    "response": "Error generating response.",
                    "score": None
                })
        
        return jsonify({"responses": responses})
    
    except Exception as e:
        logging.error("Unexpected error: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500

def extract_rating(response_text):
    import re
    match = re.search(r'\b([1-9]|10)\b', response_text)
    return int(match.group(0)) if match else None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
