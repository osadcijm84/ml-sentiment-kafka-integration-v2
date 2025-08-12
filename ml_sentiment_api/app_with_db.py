import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_config
from config.auth import require_api_key, optional_auth, auth_config
from database.models import SentimentPrediction, TrainingData, ModelMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load the trained model and vectorizer
try:
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sentiment_model.pkl')
    vectorizer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tfidf_vectorizer.pkl')
    
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    logger.info("Model and vectorizer loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    model = None
    vectorizer = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = db_config.test_connection()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model is not None,
        'vectorizer_loaded': vectorizer is not None,
        'database_connected': db_status,
        'version': '2.0'
    })

@app.route('/api/predict', methods=['POST'])
@optional_auth
def predict_sentiment():
    """Predict sentiment with database logging"""
    try:
        # Get request data
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        # Check if model is loaded
        if model is None or vectorizer is None:
            return jsonify({'error': 'Model not available'}), 503
        
        # Make prediction
        text_vectorized = vectorizer.transform([text])
        prediction = model.predict(text_vectorized)[0]
        confidence = float(np.max(model.predict_proba(text_vectorized)))
        
        # Map prediction to sentiment
        sentiment = 'positive' if prediction == 1 else 'negative'
        
        # Save prediction to database
        prediction_obj = SentimentPrediction(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            model_version="2.0"
        )
        prediction_id = prediction_obj.save()
        
        # Prepare response
        response = {
            'text': text,
            'sentiment': sentiment,
            'confidence': confidence,
            'model_version': '2.0',
            'timestamp': datetime.now().isoformat(),
            'client': getattr(request, 'client_name', 'anonymous')
        }
        
        if prediction_id:
            response['prediction_id'] = prediction_id
        
        logger.info(f"Prediction made for client: {getattr(request, 'client_name', 'anonymous')}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/predictions', methods=['GET'])
@require_api_key
def get_predictions():
    """Get recent predictions (requires API key)"""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 100)  # Cap at 100
        
        predictions = SentimentPrediction.get_recent_predictions(limit)
        
        return jsonify({
            'predictions': predictions,
            'count': len(predictions),
            'client': request.client_name
        })
        
    except Exception as e:
        logger.error(f"Error fetching predictions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_stats():
    """Get prediction statistics (requires API key)"""
    try:
        stats = SentimentPrediction.get_prediction_stats()
        model_metrics = ModelMetrics.get_latest_metrics()
        
        return jsonify({
            'prediction_stats': stats,
            'model_metrics': model_metrics,
            'client': request.client_name
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/training-data', methods=['POST'])
@require_api_key
def add_training_data():
    """Add training data (requires API key)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Handle single record
        if isinstance(data, dict):
            data = [data]
        
        # Validate and save training data
        saved_count = 0
        for record in data:
            if 'text' not in record or 'actual_sentiment' not in record:
                continue
            
            training_data = TrainingData(
                text=record['text'],
                actual_sentiment=record['actual_sentiment'],
                rating=record.get('rating'),
                product_category=record.get('product_category'),
                data_source=record.get('data_source', 'API'),
                is_training=record.get('is_training', True),
                is_validation=record.get('is_validation', False)
            )
            
            if training_data.save():
                saved_count += 1
        
        return jsonify({
            'message': f'Successfully saved {saved_count} training records',
            'saved_count': saved_count,
            'total_submitted': len(data),
            'client': request.client_name
        })
        
    except Exception as e:
        logger.error(f"Error adding training data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/training-data', methods=['GET'])
@require_api_key
def get_training_data():
    """Get training data (requires API key)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 500)  # Cap at 500
        
        training_data = TrainingData.get_training_data(limit)
        
        return jsonify({
            'training_data': training_data,
            'count': len(training_data),
            'client': request.client_name
        })
        
    except Exception as e:
        logger.error(f"Error fetching training data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/token', methods=['POST'])
def get_auth_token():
    """Get authentication token (for demonstration)"""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({'error': 'API key is required'}), 400
        
        client_name = auth_config.verify_api_key(data['api_key'])
        if not client_name:
            return jsonify({'error': 'Invalid API key'}), 401
        
        token = auth_config.generate_token('user_123', client_name)
        
        return jsonify({
            'token': token,
            'client_name': client_name,
            'expires_in_hours': auth_config.token_expiration_hours
        })
        
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Test database connection on startup
    if db_config.test_connection():
        logger.info("Database connection successful")
    else:
        logger.warning("Database connection failed - some features may not work")
    
    # Print API keys for testing (remove in production)
    logger.info("Available API keys for testing:")
    for api_key, client_name in auth_config.api_keys.items():
        logger.info(f"  {client_name}: {api_key}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

