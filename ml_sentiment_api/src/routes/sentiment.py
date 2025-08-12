from flask import Blueprint, request, jsonify
import joblib
import os

sentiment_bp = Blueprint('sentiment', __name__)

# Load the model and vectorizer
model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sentiment_model.pkl')
vectorizer_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tfidf_vectorizer.pkl')

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

@sentiment_bp.route('/predict', methods=['POST'])
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

@sentiment_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'model': 'sentiment_analysis'})

