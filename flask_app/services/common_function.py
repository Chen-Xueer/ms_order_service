from microservice_utils.settings import logger
import boto3
import json
from flask_app.database_sessions import Database
from sqlalchemy_.ms_order_service.enum_types import ReturnActionStatus, ReturnStatus, TriggerMethod
from sqlalchemy_.ms_order_service.order import Order
from sqlalchemy_.ms_order_service.transaction import Transaction
from sqlalchemy_.ms_order_service.tenant import Tenant
from sqlalchemy import (
    MetaData,
    create_engine,
    Engine,
    make_url,
    TextClause,
    URL,
)
from dotenv import load_dotenv
import os

class DataValidation:
    def __init__(self):
        database = Database()
        self.session = database.init_session()

    def validate_required_string(self,value, field_name):
        if value is None or value == "":
            return {field_name: f"{field_name} is required"}
        return {}

    def validate_required_integer(self,value, field_name):
        if value is None or not isinstance(value, int):
            return {field_name: f"{field_name} is required and must be integer"}
        return {}

    def validate_required_boolean(self,value, field_name):
        if value is None or not isinstance(value, bool):
            return {field_name: f"{field_name} is required and must be boolean"}
        return {}

    def validate_required_list(self,value, field_name):
        if value is None or not isinstance(value, list):
            return {field_name: f"{field_name} is required and must be list of valid charger types"}
        return {}
    
    def validate_required_date(self,value, field_name):
        if value is None or not isinstance(value, str):
            return {field_name: f"{field_name} is required and must be date"}
        return {}
    
    def validate_null(self,value, field_name):
        logger.info(f"{field_name}: {value}")
        if value is None:
            return {"error_description": {field_name: f"{field_name} is required"}, "status_code": 400}
        return {}
    
    def validate_transaction_id(self,transaction_id,action):
        logger.info(f"transaction_id: {transaction_id}")
        if action in (TriggerMethod.AUTHORIZE.value,TriggerMethod.START_TRANSACTION.value):
            return {}
        else:
            if transaction_id is None:
                return {"error_description": {"transaction_id": "transaction_id is required"}, "status_code": 404}
            transaction_exists  = self.session.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
            if transaction_exists is None:
                return {"error_description": {"transaction_id": "transaction_id not found"}, "status_code": 404}
        
    def validate_tenants(self,tenant_id,action):

        tenant_exists  = self.session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if tenant_exists is None:
            # kafka out check validity of tenant with tenant management service
            return {"message": "tenant not found", "action":action,"action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},404
        return tenant_exists
    
    def validate_order(self,transaction_id):
        order_exists  = self.session.query(Order).filter(Order.transaction_id == transaction_id).first()
        if order_exists is None:
            return None
        return order_exists
    
    def validate_order_request(self,request_id):
        order_exists  = self.session.query(Order).filter(Order.request_id == request_id).first()
        if order_exists is None:
            return None
        return order_exists
    
    def validate_transaction(self,transaction_id):
        transaction_exists  = self.session.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if transaction_exists is None:
            return None
        return transaction_exists



def kafka_out(topic: str, data: dict, request_id: str):
    from kafka_app.main import kafka_app
    from kafka_app.kafka_management.kafka_topic import Topic

    try:
        kafka_app.send(
            topic=Topic(
                name=topic,
                data=data,
            ),
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Error publishing message to Kafka broker: {e}")


def kafka_out_wait_response(topic: str, data: dict, return_topic:str):
    from kafka_app.main import kafka_app
    from kafka_app.kafka_management.kafka_topic import Topic
    try:

        response = kafka_app.send(
                        topic=Topic(
                            name=topic,
                            data=data,
                            return_topic=return_topic,
                        )
                    )
        logger.info("###############################")
        logger.info(f"Response from Kafka: {response}")
        return response
    except Exception as e:
        logger.error(f"Error publishing message to Kafka broker: {e}")
        return None


