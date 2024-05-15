from microservice_utils.settings import logger
import boto3
import json
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


