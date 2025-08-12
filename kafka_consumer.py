from kafka import KafkaConsumer
import json
import logging

logging.basicConfig(level=logging.INFO, format=\"%(asctime)s - %(name)s - %(levelname)s - %(message)s\")
logger = logging.getLogger(__name__)

class KafkaConsumerService:
    def __init__(self, bootstrap_servers: list, topic: str, group_id: str):
        self.topic = topic
        self.group_id = group_id
        self.consumer = None
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=bootstrap_servers,
                auto_offset_reset=\"earliest\",  # Start consuming from the beginning of the topic
                enable_auto_commit=True,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8"))
            )
            logger.info(f"Kafka Consumer initialized for topic: {topic}, group_id: {group_id} with bootstrap servers: {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Error initializing Kafka Consumer: {e}")

    def consume_messages(self, process_message_func):
        if not self.consumer:
            logger.error("Kafka Consumer is not initialized. Cannot consume messages.")
            return
        try:
            for message in self.consumer:
                logger.info(f"Received message: {message.value} from topic {message.topic} partition {message.partition} offset {message.offset}")
                process_message_func(message.value)
        except Exception as e:
            logger.error(f"Error consuming messages from Kafka: {e}")

    def close(self):
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka Consumer closed.")


