import os
import sys
import logging
import json
from kafka_consumer import KafkaConsumerService

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import db_config
from database.models import SentimentPrediction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\'
)
logger = logging.getLogger(__name__)

def process_prediction_message(message_value):
    logger.info(f"Processing message: {message_value}")
    try:
        # Assuming message_value is already a dict from deserializer
        text = message_value.get("text")
        sentiment = message_value.get("sentiment")
        confidence = message_value.get("confidence")
        model_version = message_value.get("model_version", "2.0")
        
        if not all([text, sentiment, confidence is not None]):
            logger.error(f"Invalid message format: {message_value}")
            return

        # Save prediction to database (if not already saved by API)
        # This consumer acts as a fallback or for other Kafka producers
        prediction_obj = SentimentPrediction(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            model_version=model_version
        )
        prediction_id = prediction_obj.save()
        if prediction_id:
            logger.info(f"Prediction from Kafka saved to DB with ID: {prediction_id}")
        else:
            logger.warning("Prediction from Kafka not saved to DB (might be duplicate or error).")

    except Exception as e:
        logger.error(f"Error processing Kafka message: {e}")

if __name__ == "__main__":
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "sentiment_predictions")
    kafka_group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "sentiment_group")

    logger.info(f"Starting Kafka Consumer Service for topic: {kafka_topic}, group_id: {kafka_group_id}")

    # Test database connection on startup
    if db_config.test_connection():
        logger.info("Database connection successful for consumer service")
    else:
        logger.error("Database connection failed for consumer service - exiting.")
        sys.exit(1)

    consumer_service = KafkaConsumerService(
        bootstrap_servers=kafka_bootstrap_servers.split(","),
        topic=kafka_topic,
        group_id=kafka_group_id
    )

    try:
        consumer_service.consume_messages(process_prediction_message)
    except KeyboardInterrupt:
        logger.info("Kafka Consumer Service stopped by user.")
    finally:
        consumer_service.close()


