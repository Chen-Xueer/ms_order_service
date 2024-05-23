from flask_restx import fields, Namespace
from flask_restx import reqparse

class ResponseModel:
    def __init__(self, namespace: Namespace) -> None:
        self.namespace = namespace
    
    def create_order(self):
        #meta_model=self.namespace.model('meta',{
        #    "request_id": fields.String(description="request_id", required=False),
        #    "timestamp": fields.DateTime(description="timestamp", required=False),
        #    "producer": fields.String(description="producer", required=False),
        #    "version": fields.String(description="version", required=False),
        #    "type": fields.String(description="type", required=False),
        #    "action": fields.String(description="action", required=False)
        #})
#
        #data_model=self.namespace.model('data',{
        #    "id_tag": fields.String(description="rfid", required=False),
        #    "transaction_id": fields.Integer(description="transaction_id", required=False),
        #    "charge_point_id": fields.String(description="charge_point_id", required=False),
        #    "connector_id": fields.Integer(description="connector_id", required=False),
        #    "driver_id": fields.String(description="driver_id", required=False),
        #    "trigger_method": fields.String(description="trigger_method", required=False),
        #    "start_time": fields.DateTime(description="start_time", required=False),
        #    "is_reservation": fields.Boolean(description="is_reservation", required=False),
        #    "is_charging": fields.Boolean(description="is_charging", required=False),
        #    "tenant_id": fields.String(description="tenant_id", required=False),
        #    "requires_payment": fields.Boolean(description="payment_required", required=False),
        #    "status": fields.String(description="status", required=False),
        #    "status_code": fields.Integer(description="status_code", required=False),
        #})

        data_models = {
            "meta": fields.Raw(description="meta", required=False,skip_none=True),
            "evse": fields.Raw(description="evse", required=False,skip_none=True),
            "data": fields.Raw(description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderResponseModel", data_models)
    
class RequestModel:
    def __init__(self, namespace: Namespace) -> None:
        self.namespace = namespace
    
    def create_order_mobile(self):
        meta_model=self.namespace.model('meta_create_order',{
            "request_id": fields.String(description="request_id", required=False,default="req-MUserA-1"),
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "producer": fields.String(description="producer", required=False,default="OCPP as a Service"),
            "version": fields.String(description="version", required=False,default="ocpp_incoming_message"),
            "type": fields.String(description="type", required=False,default="CreateOrder"),
        })

        evse_model=self.namespace.model('evse_create_order',{
            "charge_point_id": fields.String(description="charge_point_id", required=False,default="test_add_evse1"),
            "subprotocol": fields.String(description="subprotocol", required=False,default="ocpp1.6"),
        })

        data_model=self.namespace.model('data_create_order',{
            "connector_id": fields.Integer(description="connector_id", required=False,default=1),
            "id_tag": fields.String(description="id_tag", required=False,default="MUserA")
        })

        data_models = {
            "meta": fields.Nested(meta_model,description="meta", required=False,skip_none=True),
            "evse": fields.Nested(evse_model,description="evse", required=False,skip_none=True),
            "data": fields.Nested(data_model,description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderMobileRequestModel", data_models)
        
    def create_order_rfid(self):
        meta_model=self.namespace.model('meta_create_order_rfid',{
            "request_id": fields.String(description="request_id", required=False,default="req-MUserA-1"),
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "producer": fields.String(description="producer", required=False,default="OCPP as a Service"),
            "version": fields.String(description="version", required=False,default="ocpp_incoming_message"),
            "type": fields.String(description="type", required=False,default="CreateOrder"),
        })

        evse_model=self.namespace.model('evse_create_order_rfid',{
            "charge_point_id": fields.String(description="charge_point_id", required=False,default="test_add_evse1"),
            "subprotocol": fields.String(description="subprotocol", required=False,default="ocpp1.6"),
        })

        data_model=self.namespace.model('data_create_order_rfid',{
            "charge_point_id": fields.String(description="charge_point_id", required=False,default="cp-1"),
            "connector_id": fields.Integer(description="connector_id", required=False,default=1),
            "id_tag": fields.String(description="id_tag", required=False,default="MUserA"),
            "meter_start": fields.Integer(description="meter_start", required=False,default=1000),
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "reservation_id": fields.Integer(description="reservation_id", required=False,default=0),
            "trigger_method": fields.String(description="trigger_method", required=False,default="authorization/remote_start/make_reservation/start_transaction"),
            "start_time": fields.String(description="start_time", required=False,default="2021-09-01 00:00:00"),
            "requires_payment": fields.Boolean(description="payment_required", required=False,default=False),
        })

        data_models = {
            "meta": fields.Nested(meta_model,description="meta", required=False,skip_none=True),
            "evse": fields.Nested(evse_model,description="evse", required=False,skip_none=True),
            "data": fields.Nested(data_model,description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderRfidRequestModel", data_models)
    

        
    