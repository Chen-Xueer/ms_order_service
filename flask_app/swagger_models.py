from flask_restx import fields, Namespace
from flask_restx import reqparse

class ResponseModel:
    def __init__(self, namespace: Namespace) -> None:
        self.namespace = namespace
    
    def create_order(self):
        data_models = {
            "meta": fields.Raw(description="meta", required=False,skip_none=True),
            "evse": fields.Raw(description="evse", required=False,skip_none=True),
            "data": fields.Raw(description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderResponseModel", data_models)
    
    def list_order(self):
        order_details=self.namespace.model('data_list_order',{
            "transaction_id": fields.Integer(description="transaction_id", required=False),
            "status": fields.String(description="status", required=False),
            "charge_point_id": fields.String(description="charge_point_id", required=False),
            "connector_id": fields.Integer(description="connector_id", required=False),
            "ev_driver_id": fields.String(description="driver_id", required=False),
            "is_charging": fields.Boolean(description="is_charging", required=False),
            "is_reservation": fields.Boolean(description="is_reservation", required=False),
            "requires_payment": fields.Boolean(description="requires_payment", required=False),
            "paid_by": fields.String(description="paid_by", required=False),
            "start_time": fields.String(description="start_time", required=False),
            "end_time": fields.String(description="end_time", required=False),
            "duration": fields.Integer(description="duration", required=False),
            "charged_energy": fields.Float(description="charged_energy", required=False),
            "amount": fields.String(description="amount", required=False),
            "transaction_detail": fields.String(description="transaction_detail", required=False),
            "total_cost": fields.Float(description="amount", required=False),
            "driver": fields.String(description="driver", required=False),
            "email": fields.String(description="email", required=False),
            "start": fields.DateTime(description="start_time", required=False),
            "stop": fields.DateTime(description="stop", required=False),
            "site_name": fields.String(description="site", required=False),
            "device_name": fields.String(description="device", required=False),        
        })

        error_model = self.namespace.model('error', {
            "mobile_id": fields.String(required=False, description="mobile_id"),
            "email": fields.String(required=False, description="email"),
        })

        data_models = {
            "data": fields.Nested(order_details, description="Response", required=False,skip_none=True),
            "action": fields.String(required=True, description="action"),
            "action_status": fields.String(required=True, description="action_status"),
            "request_id": fields.String(required=True, description="request_id"),
            "status": fields.String(required=True, description="status"),
            "message": fields.String(required=False, description="message"),
            "errors": fields.Nested(error_model, description="error", required=False,skip_none=True),
        }

        return self.namespace.model("ListOrderResponseModel", data_models)
    
class RequestModel:
    def __init__(self, namespace: Namespace) -> None:
        self.namespace = namespace
    
    def create_order_mobile(self):
        meta_model=self.namespace.model('meta_create_order',{
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "producer": fields.String(description="producer", required=False,default="OCPP as a Service"),
            "version": fields.String(description="version", required=False,default="ocpp_incoming_message"),
            "type": fields.String(description="type", required=False,default="CreateOrder"),
            "action": fields.String(description="action", required=False,default="RemoteStartTransaction"),
            "tenant_id": fields.String(description="tenant_id", required=False,default="9d6cb027-ad74-4635-987c-e54b734c3516"),
        })

        evse_model=self.namespace.model('evse_create_order',{
            "charge_point_id": fields.String(description="charge_point_id", required=False,default="test_add_evse1"),
            "subprotocol": fields.String(description="subprotocol", required=False,default="ocpp1.6"),
        })

        data_model=self.namespace.model('data_create_order',{
            "connector_id": fields.Integer(description="connector_id", required=False,default=1),
            "id_tag": fields.String(description="id_tag", required=False,default="xnxpapqidmjsts3twlws"),
        })

        data_models = {
            "meta": fields.Nested(meta_model,description="meta", required=False,skip_none=True),
            "evse": fields.Nested(evse_model,description="evse", required=False,skip_none=True),
            "data": fields.Nested(data_model,description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderMobileRequestModel", data_models)
    

    def create_order_reservation(self):
        meta_model=self.namespace.model('meta_create_order_reservation',{
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "producer": fields.String(description="producer", required=False,default="oneems_charger_management"),
            "version": fields.String(description="version", required=False,default="ocpp_incoming_message"),
            "type": fields.String(description="type", required=False,default="ReservationRequest"),
            "action": fields.String(description="action", required=False,default="ReserveNow"),
            "tenant_id": fields.String(description="tenant_id", required=False,default="9d6cb027-ad74-4635-987c-e54b734c3516"),
        })

        evse_model=self.namespace.model('evse_create_order_reservation',{
            "charge_point_id": fields.String(description="charge_point_id", required=False,default="test_add_evse1"),
            "subprotocol": fields.String(description="subprotocol", required=False,default="ocpp1.6"),
        })

        data_model=self.namespace.model('data_create_order_reservation',{
            "connector_id": fields.Integer(description="connector_id", required=False,default=0),
            "id_tag": fields.String(description="id_tag", required=False,default="xnxpapqidmjsts3twlws"),
            "requires_payment": fields.Boolean(description="requires_payment", required=False,default=False),
        })

        data_models = {
            "meta": fields.Nested(meta_model,description="meta", required=False,skip_none=True),
            "evse": fields.Nested(evse_model,description="evse", required=False,skip_none=True),
            "data": fields.Nested(data_model,description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderRfidReservationRequestModel", data_models)
    
    def create_order_stop_transaction(self):
        meta_model=self.namespace.model('meta_create_order_stop_transaction',{
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "producer": fields.String(description="producer", required=False,default="OCPP as a Service"),
            "version": fields.String(description="version", required=False,default="ocpp_incoming_message"),
            "type": fields.String(description="type", required=False,default="StopTransaction"),
            "action": fields.String(description="action", required=False,default="RemoteStopTransaction"),
        })

        evse_model=self.namespace.model('evse_create_order_stop_transaction',{
            "charge_point_id": fields.String(description="charge_point_id", required=False,default="test_add_evse1"),
            "subprotocol": fields.String(description="subprotocol", required=False,default="ocpp1.6"),
        })

        data_model=self.namespace.model('data_create_order_stop_transaction',{
            "meter_stop": fields.Integer(description="meter_stop", required=False,default=0),
            "id_tag": fields.String(description="id_tag", required=False,default="xnxpapqidmjsts3twlws"),
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "transaction_id": fields.Integer(description="transaction_id", required=False,default=0),
            "reason": fields.String(description="reason", required=False,default="Remote"),
            "transaction_data": fields.String(description="transaction_data", required=False,default=""),
        })

        data_models = {
            "meta": fields.Nested(meta_model,description="meta", required=False,skip_none=True),
            "evse": fields.Nested(evse_model,description="evse", required=False,skip_none=True),
            "data": fields.Nested(data_model,description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderRfidStopTransactionRequestModel", data_models)

    def list_order(self):
        data_models = {
            "keyword": fields.String(description="start_time", required=False,default="2021-09-01 00:00:00"),
        }
        return self.namespace.model("ListOrderRequestModel", data_models)
    

    def create_order_authorize(self):
        meta_model=self.namespace.model('meta_create_order_authorize',{
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "producer": fields.String(description="producer", required=False,default="OCPP as a Service"),
            "version": fields.String(description="version", required=False,default="ocpp_incoming_message"),
            "type": fields.String(description="type", required=False,default="AuthorizeRequest"),
            "action": fields.String(description="action", required=False,default="Authorize"),
            "tenant_id": fields.String(description="tenant_id", required=False,default="9d6cb027-ad74-4635-987c-e54b734c3516"),
        })

        evse_model=self.namespace.model('evse_create_order_authorize',{
            "charge_point_id": fields.String(description="charge_point_id", required=False,default="test_add_evse1"),
            "subprotocol": fields.String(description="subprotocol", required=False,default="ocpp1.6"),
        })

        data_model=self.namespace.model('data_create_order_authorize',{
            "id_tag": fields.String(description="id_tag", required=False,default="xnxpapqidmjsts3twlws"),
        })

        data_models = {
            "meta": fields.Nested(meta_model,description="meta", required=False,skip_none=True),
            "evse": fields.Nested(evse_model,description="evse", required=False,skip_none=True),
            "data": fields.Nested(data_model,description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderAuthorizeRequestModel", data_models)

    def create_order_remote_start(self):
        meta_model=self.namespace.model('meta_create_order_remote_start',{
            "timestamp": fields.String(description="timestamp", required=False,default="2021-09-01 00:00:00"),
            "producer": fields.String(description="producer", required=False,default="oneems_charger_management"),
            "version": fields.String(description="version", required=False,default="ocpp_incoming_message"),
            "type": fields.String(description="type", required=False,default="CreateOrder"),
            "action": fields.String(description="action", required=False,default="RemoteStartTransaction"),
            "tenant_id": fields.String(description="tenant_id", required=False,default="9d6cb027-ad74-4635-987c-e54b734c3516"),
        })

        evse_model=self.namespace.model('evse_create_order_remote_start',{
            "charge_point_id": fields.String(description="charge_point_id", required=False,default="SGEVCharger"),
            "subprotocol": fields.String(description="subprotocol", required=False,default="ocpp1.6"),
        })

        data_model=self.namespace.model('data_create_order_remote_start',{
            "connector_id": fields.Integer(description="connector_id", required=False,default=1),
            "id_tag": fields.String(description="id_tag", required=False,default="xnxpapqidmjsts3twlws"),
        })

        data_models = {
            "meta": fields.Nested(meta_model,description="meta", required=False,skip_none=True),
            "evse": fields.Nested(evse_model,description="evse", required=False,skip_none=True),
            "data": fields.Nested(data_model,description="data", required=False,skip_none=True),
        }
        return self.namespace.model("CreateOrderRemoteStartRequestModel", data_models)


    def none_data(self):
        return self.namespace.model("NoneDataRequestModel", {})
    

        
    