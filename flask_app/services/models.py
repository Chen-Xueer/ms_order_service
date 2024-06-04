from dataclasses import dataclass, fields
from typing import Optional

@dataclass(init=False)
class KafkaPayload:
    timestamp: Optional[str] = None
    version: Optional[str] = None
    meta_type: Optional[str] = None
    action: Optional[str] = None
    producer: Optional[str] = None
    request_id: Optional[str] = None
    transaction_id: Optional[str] = None
    charge_point_id: Optional[str] = None
    subprotocol: Optional[str] = None
    connector_id: Optional[str] = None
    start_time: Optional[str] = None
    id_tag: Optional[str] = None
    is_charging: Optional[bool] = None
    is_reservation: Optional[bool] = None
    requires_payment: Optional[bool] = None
    tenant_id: Optional[str] = None
    trigger_method: Optional[str] = None
    status_code: Optional[str] = None
    id_tag_status: Optional[str] = None
    expiry_date: Optional[str] = None

    def __init__(self, **kwargs):
        self.timestamp = kwargs.get("meta", {}).get("producer")
        self.version = kwargs.get("meta", {}).get("version")
        self.meta_type = kwargs.get("meta", {}).get("type")
        self.action = kwargs.get("meta", {}).get("action")
        self.producer = kwargs.get("meta", {}).get("producer")
        self.request_id = kwargs.get("meta", {}).get("request_id")
        self.charge_point_id = kwargs.get("evse", {}).get("charge_point_id")
        self.subprotocol = kwargs.get("evse", {}).get("subprotocol")
        self.transaction_id = kwargs.get("data", {}).get("transaction_id")
        self.connector_id = kwargs.get("data", {}).get("connector_id")
        self.start_time = kwargs.get("data", {}).get("start_time")
        self.id_tag = kwargs.get("data", {}).get("id_tag")
        self.is_charging = kwargs.get("data", {}).get("is_charging")
        self.is_reservation = kwargs.get("data", {}).get("is_reservation")
        self.requires_payment = kwargs.get("data", {}).get("requires_payment")
        self.tenant_id = kwargs.get("data", {}).get("tenant_id")
        self.trigger_method = kwargs.get("data", {}).get("trigger_method")
        self.status_code = kwargs.get("data", {}).get("status_code")
        self.id_tag_status = kwargs.get("data", {}).get("id_tag_status")
        self.expiry_dt = kwargs.get("data", {}).get("expiry_date")
    
    def to_dict(self):
        return {
            "meta": {
                "timestamp": self.timestamp,
                "version": self.version,
                "type": self.meta_type,
                "action": self.action,
                "producer": self.producer,
                "request_id": self.request_id
            },
            "evse": {
                "charge_point_id": self.charge_point_id,
                "subprotocol": self.subprotocol
            },
            "data": {
                "transaction_id": self.transaction_id,
                "charge_point_id": self.charge_point_id,
                "connector_id": self.connector_id,
                "start_time": self.start_time,
                "id_tag": self.id_tag,
                "is_charging": self.is_charging,
                "is_reservation": self.is_reservation,
                "requires_payment": self.requires_payment,
                "tenant_id": self.tenant_id,
                "trigger_method": self.trigger_method,
                "status_code": self.status_code,
                "id_tag_status": self.id_tag_status,
                "expiry_dt": self.expiry_dt
            }
        }


@dataclass(init=False)
class ReservationPayload:
    connector_id: Optional[str] = None
    expiry_date: Optional[str] = None
    id_tag: Optional[str] = None
    reservation_id: Optional[int] = None

    timestamp: Optional[str] = None
    version: Optional[str] = None
    meta_type: Optional[str] = None
    action: Optional[str] = None
    producer: Optional[str] = None
    request_id: Optional[str] = None
    charge_point_id: Optional[str] = None
    subprotocol: Optional[str] = None

    def to_dict(self):
        return {
            "meta": {
                "timestamp": self.timestamp,
                "version": self.version,
                "type": self.meta_type,
                "action": self.action,
                "producer": self.producer,
                "request_id": self.request_id
            },
            "evse": {
                "charge_point_id": self.charge_point_id,
                "subprotocol": self.subprotocol
            },
            "data": {
                "reservation_id": self.reservation_id,
                "connector_id": self.connector_id,
                "expiry_date": self.expiry_date,
                "id_tag": self.id_tag
            }
        }


@dataclass(init=False)
class StartTransactionPayload:
    transaction_id: Optional[str] = None
    status: Optional[str] = None
    parent_id_tag: Optional[str] = None
    expiry_date: Optional[str] = None

    timestamp: Optional[str] = None
    version: Optional[str] = None
    meta_type: Optional[str] = None
    action: Optional[str] = None
    producer: Optional[str] = None
    request_id: Optional[str] = None
    charge_point_id: Optional[str] = None
    subprotocol: Optional[str] = None

    def to_dict(self):
        return {
            "meta": {
                "timestamp": self.timestamp,
                "version": self.version,
                "type": self.meta_type,
                "action": self.action,
                "producer": self.producer,
                "request_id": self.request_id
            },
            "evse": {
                "charge_point_id": self.charge_point_id,
                "subprotocol": self.subprotocol
            },
            "data":{   
                "transaction_id": self.transaction_id,
                "id_tag_info": {
                    "status": self.status,
                    "parent_id_tag": self.parent_id_tag,
                    "expiry_date": self.expiry_date
                }
            }
        }
