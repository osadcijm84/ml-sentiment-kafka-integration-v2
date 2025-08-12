import os
import sys
from flask import Flask, request, jsonify
import joblib

app = Flask(__name__)

# Load the model and vectorizer
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sentiment_model.pkl')
vectorizer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tfidf_vectorizer.pkl')

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

@app.route('/api/predict', methods=['POST'])
def predict_sentiment():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Vectorize the text
        text_vectorized = vectorizer.transform([text])
        
        # Make prediction
        prediction = model.predict(text_vectorized)[0]
        probability = model.predict_proba(text_vectorized)[0]
        
        sentiment = 'positive' if prediction == 1 else 'negative'
        confidence = max(probability)
        
        return jsonify({
            'text': text,
            'sentiment': sentiment,
            'confidence': float(confidence)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'model': 'sentiment_analysis'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
