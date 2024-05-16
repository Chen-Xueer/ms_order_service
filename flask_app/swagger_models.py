from flask_restx import fields, Namespace
from flask_restx import reqparse

class ResponseModel:
    def __init__(self, namespace: Namespace) -> None:
        self.namespace = namespace
    
    def create_order(self):
        meta_model={
            "request_id": fields.String(description="request_id", required=True),
            "timestamp": fields.DateTime(description="timestamp", required=True),
            "producer": fields.String(description="producer", required=True),
            "version": fields.String(description="version", required=True),
            "type": fields.String(description="type", required=True),
            "action": fields.String(description="action", required=True)
        }

        data_model={
            "rfid": fields.String(description="rfid", required=False),
            "transaction_id": fields.Integer(description="transaction_id", required=True),
            "charge_point_id": fields.String(description="charge_point_id", required=True),
            "connector_id": fields.Integer(description="connector_id", required=True),
            "driver_id": fields.String(description="driver_id", required=True),
            "trigger_method": fields.String(description="trigger_method", required=True),
            "start_time": fields.DateTime(description="start_time", required=True),
            "is_reservation": fields.Boolean(description="is_reservation", required=True),
            "is_charging": fields.Boolean(description="is_charging", required=True),
            "tenant_id": fields.String(description="tenant_id", required=True),
            "payment_required_ind": fields.Boolean(description="payment_required", required=True),
            "status": fields.String(description="status", required=True),
            "status_code": fields.Integer(description="status_code", required=True),
        }

        data_models = {
            "meta": fields.Nested(meta_model, description="meta", required=False,skip_none=True),
            "data": fields.Nested(data_model, description="data", required=True,skip_none=True),
        }
        return self.namespace.model("CreateOrderResponseModel", data_models)
    
class RequestModel:
    def __init__(self, namespace: Namespace) -> None:
        self.namespace = namespace
    
    def create_order(self):
        meta_model={
            "request_id": fields.String(description="request_id", required=True),
            "timestamp": fields.DateTime(description="timestamp", required=True),
            "producer": fields.String(description="producer", required=True),
            "version": fields.String(description="version", required=True),
            "type": fields.String(description="type", required=True),
            "action": fields.String(description="action", required=True)
        }

        data_model={
            "rfid": fields.String(description="rfid", required=False),
            "charge_point_id": fields.String(description="charge_point_id", required=True),
            "connector_id": fields.Integer(description="connector_id", required=True),
            "driver_id": fields.String(description="driver_id", required=True),
            "trigger_method": fields.String(description="trigger_method", required=True),
            "start_time": fields.DateTime(description="start_time", required=True),
            "is_reservation": fields.Boolean(description="is_reservation", required=True),
            "is_charging": fields.Boolean(description="is_charging", required=True),
            "tenant_id": fields.String(description="tenant_id", required=True),
            "payment_required_ind": fields.Boolean(description="payment_required", required=True)
        }

        data_models = {
            "meta": fields.Nested(meta_model, description="meta", required=False,skip_none=True),
            "data": fields.Nested(data_model, description="data", required=True,skip_none=True),
        }
        return self.namespace.model("CreateOrderRequestModel", data_models)
    

        
    