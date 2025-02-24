import os
import logging
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set the OPENAI_API_KEY environment variable.")
openai.api_key = OPENAI_API_KEY

# Define AI personas
personas = {
    "CMO": "You are a Chief Marketing Officer. Provide insights on go-to-market strategy and pricing.",
    "CTO": "You are a Chief Technology Officer. Evaluate technical feasibility and development timelines.",
    "CFO": "You are a Chief Financial Officer. Analyze financial projections and funding requirements.",
    "Legal Advisor": "You are a Legal Advisor. Assess legal considerations for fundraising and M&A.",
    "Business Analyst": "You are a Business Analyst. Conduct market and competitive analysis."
}

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    if not data or "business_idea" not in data:
        return jsonify({"error": "No business idea provided"}), 400
    
    business_idea = data["business_idea"]
    logging.info(f"Received request data: {data}")
    
    responses = {}
    for role, prompt_intro in personas.items():
        messages = [
            {"role": "system", "content": prompt_intro},
            {"role": "user", "content": f"Business Idea: {business_idea}. What are your thoughts?"}
        ]
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # Change model as needed
                messages=messages
            )
            responses[role] = response["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Error generating response for {role}: {str(e)}")
            responses[role] = "Error generating response."
    
    return jsonify(responses)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
