from flask import Flask, request, jsonify
import openai
import logging
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Define personas
personas = [
    {"name": "CMO", "role": "Chief Marketing Officer", "expertise": "go-to-market and pricing strategies"},
    {"name": "CTO", "role": "Chief Technology Officer", "expertise": "technology feasibility and product development"},
    {"name": "CFO", "role": "Chief Financial Officer", "expertise": "financial modeling and projections"},
    {"name": "Legal Advisor", "role": "Legal Expert", "expertise": "M&A transactions and fundraising legal considerations"},
    {"name": "Business Analyst", "role": "Market Analyst", "expertise": "competitive and market analysis"}
]

def generate_response(persona, business_idea):
    """Generate a response from a persona based on the business idea."""
    prompt = (
        f"You are a {persona['role']} specializing in {persona['expertise']}. "
        f"Provide insights on the following business idea: '{business_idea}'. "
        f"Give a response and a score from 1-10 on feasibility and market potential."
    )
    
    try:
        response = openai_client.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200
        )
        text_response = response.choices[0].message.content.strip()
        score = int(''.join(filter(str.isdigit, text_response[:3])) or 5)  # Extract first digit or default to 5
        return text_response, min(max(score, 1), 10)  # Ensure score is within 1-10
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "Error generating response", 5

@app.route("/ask", methods=["POST"])
def ask():
    """Handles POST requests to generate responses from advisory board personas."""
    try:
        data = request.get_json()
        logging.info(f"Received request data: {data}")
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        business_idea = data.get("business_idea")
        if not business_idea:
            return jsonify({"error": "No business idea provided"}), 400
        
        responses = []
        for persona in personas:
            response_text, score = generate_response(persona, business_idea)
            responses.append({
                "persona": persona["name"],
                "response": response_text,
                "score": score
            })
        
        return jsonify(responses)
    except Exception as e:
        logging.error(f"Error in /ask endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
