from kafka_app.kafka_management.kafka_app import KafkaApp
from dotenv import load_dotenv
import os
from microservice_utils.settings import logger

load_dotenv(".env.testing")
logger.info("Initialize kafka: " + os.getenv("KAFKA_BOOTSTRAP_SERVER") + " " + os.getenv("KAFKA_SASL_USERNAME") + " " + os.getenv("KAFKA_SASL_PASSWORD"))

kafka_app = KafkaApp(
    service_name=os.environ.get("MASTER_DB_NAME", ""),
    brokers=os.environ.get("KAFKA_BOOTSTRAP_SERVER"),
    #security_protocol = "SASL_SSL",
    #sasl_mechanism="SCRAM-SHA-512",
    sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
    sasl_password=os.environ.get("KAFKA_SASL_PASSWORD", ""),
    _response_timeout=120
)
