from ms_tools.kafka_management.kafka_app import KafkaApp
from dotenv import load_dotenv
import os
from microservice_utils.settings import logger
from ms_tools.kafka_management.topics import MsEvDriverManagement,MsPaymentManagement,MsOrderManagement

load_dotenv(".env.testing")
logger.info("Initialize kafka: " + os.getenv("KAFKA_BOOTSTRAP_SERVER") + " " + os.getenv("KAFKA_SASL_USERNAME") + " " + os.getenv("KAFKA_SASL_PASSWORD"))

topics = tuple([e.value for e in MsEvDriverManagement]+[e.value for e in MsPaymentManagement]+[e.value for e in MsOrderManagement])

kafka_app = KafkaApp(
    topic_list=topics,
    service_name=os.environ.get("MASTER_DB_NAME", ""),
    brokers=os.environ.get("KAFKA_BOOTSTRAP_SERVER"),
    sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
    sasl_password=os.environ.get("KAFKA_SASL_PASSWORD", ""),
    _router_response_timeout=60
)