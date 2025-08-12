from kafka import KafkaProducer
import json
import logging

logging.basicConfig(level=logging.INFO, format=\"%(asctime)s - %(name)s - %(levelname)s - %(message)s\")
logger = logging.getLogger(__name__)

class KafkaProducerService:
    def __init__(self, bootstrap_servers: list, topic: str):
        self.topic = topic
        self.producer = None
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks=\"all\",  # Ensure all replicas acknowledge the message
                retries=3,     # Retry sending if fails
                linger_ms=10,  # Send messages in batches
            )
            logger.info(f"Kafka Producer initialized for topic: {topic} with bootstrap servers: {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Error initializing Kafka Producer: {e}")

    def send_message(self, message: dict):
        if not self.producer:
            logger.error("Kafka Producer is not initialized. Cannot send message.")
            return
        try:
            future = self.producer.send(self.topic, message)
            record_metadata = future.get(timeout=10)  # Block until message is sent or timeout
            logger.info(f"Message sent to Kafka topic {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {e}")

    def close(self):
        if self.producer:
            self.producer.close()
            logger.info("Kafka Producer closed.")


