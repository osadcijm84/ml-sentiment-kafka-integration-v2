import pyodbc
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.database import db_config

logger = logging.getLogger(__name__)

class SentimentPrediction:
    """Model for sentiment predictions"""
    
    def __init__(self, text: str, sentiment: str, confidence: float, 
                 model_version: str = "1.0"):
        self.text = text
        self.sentiment = sentiment
        self.confidence = confidence
        self.model_version = model_version
        self.prediction_date = datetime.now()
    
    def save(self) -> Optional[int]:
        """Save prediction to database"""
        try:
            conn = db_config.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            query = """
                INSERT INTO SentimentPredictions 
                (text, sentiment, confidence, prediction_date, model_version)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                self.text, self.sentiment, self.confidence, 
                self.prediction_date, self.model_version
            ))
            
            # Get the inserted ID
            cursor.execute("SELECT @@IDENTITY")
            prediction_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved prediction with ID: {prediction_id}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"Error saving prediction: {str(e)}")
            return None
    
    @staticmethod
    def get_recent_predictions(limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent predictions from database"""
        try:
            conn = db_config.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            query = """
                SELECT TOP (?) id, text, sentiment, confidence, 
                       prediction_date, model_version
                FROM SentimentPredictions
                ORDER BY prediction_date DESC
            """
            cursor.execute(query, (limit,))
            
            predictions = []
            for row in cursor.fetchall():
                predictions.append({
                    'id': row[0],
                    'text': row[1],
                    'sentiment': row[2],
                    'confidence': row[3],
                    'prediction_date': row[4].isoformat() if row[4] else None,
                    'model_version': row[5]
                })
            
            conn.close()
            return predictions
            
        except Exception as e:
            logger.error(f"Error fetching predictions: {str(e)}")
            return []
    
    @staticmethod
    def get_prediction_stats() -> Dict[str, Any]:
        """Get prediction statistics"""
        try:
            conn = db_config.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            
            # Total predictions
            cursor.execute("SELECT COUNT(*) FROM SentimentPredictions")
            total_predictions = cursor.fetchone()[0]
            
            # Sentiment distribution
            cursor.execute("""
                SELECT sentiment, COUNT(*) as count
                FROM SentimentPredictions
                GROUP BY sentiment
            """)
            sentiment_dist = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average confidence
            cursor.execute("SELECT AVG(confidence) FROM SentimentPredictions")
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            return {
                'total_predictions': total_predictions,
                'sentiment_distribution': sentiment_dist,
                'average_confidence': round(avg_confidence, 4)
            }
            
        except Exception as e:
            logger.error(f"Error fetching prediction stats: {str(e)}")
            return {}

class TrainingData:
    """Model for training/validation data"""
    
    def __init__(self, text: str, actual_sentiment: str, rating: float = None,
                 product_category: str = None, data_source: str = "Amazon Reviews",
                 is_training: bool = True, is_validation: bool = False):
        self.text = text
        self.actual_sentiment = actual_sentiment
        self.rating = rating
        self.product_category = product_category
        self.data_source = data_source
        self.is_training = is_training
        self.is_validation = is_validation
        self.created_at = datetime.now()
    
    def save(self) -> Optional[int]:
        """Save training data to database"""
        try:
            conn = db_config.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            query = """
                INSERT INTO TrainingData 
                (text, actual_sentiment, rating, product_category, data_source,
                 is_training, is_validation, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                self.text, self.actual_sentiment, self.rating,
                self.product_category, self.data_source,
                self.is_training, self.is_validation, self.created_at
            ))
            
            # Get the inserted ID
            cursor.execute("SELECT @@IDENTITY")
            data_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved training data with ID: {data_id}")
            return data_id
            
        except Exception as e:
            logger.error(f"Error saving training data: {str(e)}")
            return None
    
    @staticmethod
    def get_training_data(limit: int = 100) -> List[Dict[str, Any]]:
        """Get training data from database"""
        try:
            conn = db_config.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            query = """
                SELECT TOP (?) id, text, actual_sentiment, rating,
                       product_category, data_source, is_training, is_validation
                FROM TrainingData
                WHERE is_training = 1
                ORDER BY created_at DESC
            """
            cursor.execute(query, (limit,))
            
            training_data = []
            for row in cursor.fetchall():
                training_data.append({
                    'id': row[0],
                    'text': row[1],
                    'actual_sentiment': row[2],
                    'rating': row[3],
                    'product_category': row[4],
                    'data_source': row[5],
                    'is_training': bool(row[6]),
                    'is_validation': bool(row[7])
                })
            
            conn.close()
            return training_data
            
        except Exception as e:
            logger.error(f"Error fetching training data: {str(e)}")
            return []
    
    @staticmethod
    def bulk_insert(data_list: List[Dict[str, Any]]) -> int:
        """Bulk insert training data"""
        try:
            conn = db_config.get_connection()
            if not conn:
                return 0
            
            cursor = conn.cursor()
            query = """
                INSERT INTO TrainingData 
                (text, actual_sentiment, rating, product_category, data_source,
                 is_training, is_validation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            inserted_count = 0
            for data in data_list:
                try:
                    cursor.execute(query, (
                        data.get('text', ''),
                        data.get('actual_sentiment', ''),
                        data.get('rating'),
                        data.get('product_category'),
                        data.get('data_source', 'Amazon Reviews'),
                        data.get('is_training', True),
                        data.get('is_validation', False)
                    ))
                    inserted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert record: {str(e)}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"Bulk inserted {inserted_count} training records")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error bulk inserting training data: {str(e)}")
            return 0

class ModelMetrics:
    """Model for storing model performance metrics"""
    
    def __init__(self, model_version: str, accuracy: float, 
                 precision_score: float, recall_score: float, f1_score: float,
                 notes: str = None):
        self.model_version = model_version
        self.accuracy = accuracy
        self.precision_score = precision_score
        self.recall_score = recall_score
        self.f1_score = f1_score
        self.notes = notes
        self.training_date = datetime.now()
    
    def save(self) -> Optional[int]:
        """Save model metrics to database"""
        try:
            conn = db_config.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            query = """
                INSERT INTO ModelMetrics 
                (model_version, accuracy, precision_score, recall_score, 
                 f1_score, training_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                self.model_version, self.accuracy, self.precision_score,
                self.recall_score, self.f1_score, self.training_date, self.notes
            ))
            
            # Get the inserted ID
            cursor.execute("SELECT @@IDENTITY")
            metrics_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved model metrics with ID: {metrics_id}")
            return metrics_id
            
        except Exception as e:
            logger.error(f"Error saving model metrics: {str(e)}")
            return None
    
    @staticmethod
    def get_latest_metrics() -> Optional[Dict[str, Any]]:
        """Get latest model metrics"""
        try:
            conn = db_config.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            query = """
                SELECT TOP 1 model_version, accuracy, precision_score, 
                       recall_score, f1_score, training_date, notes
                FROM ModelMetrics
                ORDER BY training_date DESC
            """
            cursor.execute(query)
            row = cursor.fetchone()
            
            if row:
                metrics = {
                    'model_version': row[0],
                    'accuracy': row[1],
                    'precision_score': row[2],
                    'recall_score': row[3],
                    'f1_score': row[4],
                    'training_date': row[5].isoformat() if row[5] else None,
                    'notes': row[6]
                }
            else:
                metrics = None
            
            conn.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching model metrics: {str(e)}")
            return None

