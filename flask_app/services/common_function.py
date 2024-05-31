from microservice_utils.settings import logger
import boto3
import json
from flask_app.database_sessions import Database
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
    
    def validate_tenants(self,tenant_id):
        tenant_exists  = self.session.query(Tenant).filter(Tenant.tenant == tenant_id).first()
        if tenant_exists is None:
            # kafka out check validity of tenant with tenant management service
            return None
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


