from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()
app = Flask(__name__)
CORS(app)

HF_TOKEN = os.getenv("HF_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_pest():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Invalid file"}), 400

    try:
        # Detect pest from image
        image_data = file.read()
        pest_result = detect_pest(image_data)
        
        if "error" in pest_result:
            return jsonify(pest_result), 500
            
        # Get AI recommendations
        recommendations = get_ai_recommendations(pest_result['label'])
        return jsonify({
            "pest": pest_result['label'],
            "confidence": f"{pest_result['score']*100:.1f}%",
            "recommendations": recommendations
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def detect_pest(image_data):
    API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
    
    for _ in range(3):  # Retry logic
        response = requests.post(API_URL, headers=HEADERS, data=image_data)
        if response.status_code == 200:
            return response.json()[0]
        time.sleep(15)
    return {"error": "Pest detection failed"}

def get_ai_recommendations(pest):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    
    prompt = f"""**Task:** As a senior entomologist with 20 years experience in agricultural pest control, provide recommendations for managing {pest} infestation and get me the pesticides to kill the pest.
    
    **Response Requirements:**
    - Present in clear, concise bullet points
    - Prioritize eco-friendly solutions first
    - Include specific product names where applicable
    - Mention safety precautions
    - Avoid markdown formatting
    
    **Structure:**
    Organic Control | Chemical Treatments | Prevention | Safety"""
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": 500,
            "temperature": 0.7,
            "do_sample": True,
            "top_p": 0.9,
            "repetition_penalty": 1.2
        }
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            full_response = response.json()[0]['generated_text']
            
            # Enhanced response cleaning
            clean_response = full_response.split("**Structure:**")[-1] \
                .split("\n\nNote:")[0] \
                .replace(prompt, "") \
                .strip()
            
            return clean_response.replace("\n", "<br>")
        return "Recommendations being generated..."
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)