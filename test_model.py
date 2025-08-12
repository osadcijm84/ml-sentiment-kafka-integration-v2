import unittest
import json
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

class TestSentimentModel(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.model = joblib.load('sentiment_model.pkl')
        self.vectorizer = joblib.load('tfidf_vectorizer.pkl')
    
    def test_model_loaded(self):
        """Test that the model is loaded correctly."""
        self.assertIsNotNone(self.model)
        self.assertIsInstance(self.model, LogisticRegression)
    
    def test_vectorizer_loaded(self):
        """Test that the vectorizer is loaded correctly."""
        self.assertIsNotNone(self.vectorizer)
        self.assertIsInstance(self.vectorizer, TfidfVectorizer)
    
    def test_positive_sentiment_prediction(self):
        """Test prediction for positive sentiment."""
        positive_text = "This product is amazing and I love it!"
        text_vectorized = self.vectorizer.transform([positive_text])
        prediction = self.model.predict(text_vectorized)[0]
        self.assertEqual(prediction, 1, "Should predict positive sentiment")
    
    def test_negative_sentiment_prediction(self):
        """Test prediction for negative sentiment."""
        negative_text = "This product is terrible and I hate it!"
        text_vectorized = self.vectorizer.transform([negative_text])
        prediction = self.model.predict(text_vectorized)[0]
        self.assertEqual(prediction, 0, "Should predict negative sentiment")
    
    def test_prediction_probability(self):
        """Test that prediction probabilities are valid."""
        test_text = "This is a test review"
        text_vectorized = self.vectorizer.transform([test_text])
        probabilities = self.model.predict_proba(text_vectorized)[0]
        
        # Check that probabilities sum to 1
        self.assertAlmostEqual(sum(probabilities), 1.0, places=5)
        
        # Check that all probabilities are between 0 and 1
        for prob in probabilities:
            self.assertGreaterEqual(prob, 0.0)
            self.assertLessEqual(prob, 1.0)
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        empty_text = ""
        text_vectorized = self.vectorizer.transform([empty_text])
        prediction = self.model.predict(text_vectorized)
        self.assertIsNotNone(prediction)
    
    def test_model_accuracy_threshold(self):
        """Test that model meets minimum accuracy threshold."""
        # This is a basic test - in practice, you'd use a validation set
        test_cases = [
            ("I love this product", 1),
            ("This is amazing", 1),
            ("Great quality", 1),
            ("Terrible product", 0),
            ("I hate this", 0),
            ("Very bad quality", 0)
        ]
        
        correct_predictions = 0
        for text, expected in test_cases:
            text_vectorized = self.vectorizer.transform([text])
            prediction = self.model.predict(text_vectorized)[0]
            if prediction == expected:
                correct_predictions += 1
        
        accuracy = correct_predictions / len(test_cases)
        self.assertGreaterEqual(accuracy, 0.8, "Model accuracy should be at least 80%")

if __name__ == '__main__':
    unittest.main()

