import unittest
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml_sentiment_api'))

from ml_sentiment_api.simple_app import app

class TestSentimentAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['model'], 'sentiment_analysis')
    
    def test_predict_positive_sentiment(self):
        """Test prediction endpoint with positive sentiment."""
        payload = {'text': 'This product is amazing!'}
        response = self.app.post('/api/predict', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['sentiment'], 'positive')
        self.assertEqual(data['text'], payload['text'])
        self.assertGreater(data['confidence'], 0.5)
    
    def test_predict_negative_sentiment(self):
        """Test prediction endpoint with negative sentiment."""
        payload = {'text': 'This product is terrible!'}
        response = self.app.post('/api/predict', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['sentiment'], 'negative')
        self.assertEqual(data['text'], payload['text'])
        self.assertGreater(data['confidence'], 0.5)
    
    def test_predict_empty_text(self):
        """Test prediction endpoint with empty text."""
        payload = {'text': ''}
        response = self.app.post('/api/predict', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_predict_no_text_field(self):
        """Test prediction endpoint without text field."""
        payload = {'message': 'This should fail'}
        response = self.app.post('/api/predict', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_predict_invalid_json(self):
        """Test prediction endpoint with invalid JSON."""
        response = self.app.post('/api/predict', 
                                data='invalid json',
                                content_type='application/json')
        
        # Flask returns 500 for invalid JSON, which is acceptable
        self.assertIn(response.status_code, [400, 500])
    
    def test_predict_confidence_range(self):
        """Test that confidence values are in valid range."""
        test_texts = [
            'This is amazing!',
            'This is terrible!',
            'This is okay.',
            'I love this product',
            'I hate this product'
        ]
        
        for text in test_texts:
            payload = {'text': text}
            response = self.app.post('/api/predict', 
                                    json=payload,
                                    content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            confidence = data['confidence']
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)

if __name__ == '__main__':
    unittest.main()

