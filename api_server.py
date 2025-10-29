from flask import Flask, request, jsonify
from flask_cors import CORS
from chroma_vector_store import query_with_context
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)  # Allow requests from VR app

@app.route('/query', methods=['POST'])
def query():
    """
    Endpoint for VR app to ask questions.
    Expects JSON: {"question": "your question here"}
    Returns JSON: {"answer": "the answer", "latency": 1.23}
    """
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    try:
        answer, latency = query_with_context(question)
        return jsonify({
            'answer': answer,
            'latency': latency
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Check if server is running"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("Starting VR Q&A API Server...")
    print("Endpoint: http://localhost:5000/query")
    app.run(host='0.0.0.0', port=5000, debug=True)

# Jetson linux setup
# APi calls form the VR
# figure out university networking