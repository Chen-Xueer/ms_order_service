from dataclasses import dataclass, fields, asdict
from typing import List, Optional

from sqlalchemy_.ms_order_service.enum_types import StopTransactionReason

@dataclass(init=False)
class KafkaMeta:
    timestamp: Optional[str] = None
    version: Optional[str] = None
    meta_type: Optional[str] = None
    action: Optional[str] = None
    producer: Optional[str] = None
    request_id: Optional[str] = None

    def __init__(self, **kwargs):
        self.timestamp = kwargs.get("timestamp")
        self.version = kwargs.get("version")
        self.meta_type = kwargs.get("type")
        self.action = kwargs.get("action")
        self.producer = kwargs.get("producer")
        self.request_id = kwargs.get("request_id")
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "version": self.version,
            "type": self.meta_type,
            "action": self.action,
            "producer": self.producer,
            "request_id": self.request_id
        }

@dataclass(init=False)
class KafkaEVSE:
    charge_point_id: Optional[str] = None
    subprotocol: Optional[str] = None

    def __init__(self, **kwargs):
        self.charge_point_id = kwargs.get("charge_point_id")
        self.subprotocol = kwargs.get("subprotocol")
    
    def to_dict(self):
        return asdict(self)


@dataclass(init=False)
class KafkaPayload:
    meta: KafkaMeta
    evse: KafkaEVSE
    transaction_id: Optional[str] = None
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
    keyword: Optional[str] = None

    def __init__(self, **kwargs):
        self.meta = KafkaMeta(**kwargs.get("meta", {}))
        self.evse = KafkaEVSE(**kwargs.get("evse", {}))
        data = kwargs.get("data", {})
        self.transaction_id = data.get("transaction_id")
        self.connector_id = data.get("connector_id")
        self.start_time = data.get("start_time")
        self.id_tag = data.get("id_tag")
        self.is_charging = data.get("is_charging")
        self.is_reservation = data.get("is_reservation")
        self.requires_payment = data.get("requires_payment")
        self.tenant_id = data.get("tenant_id")
        self.trigger_method = data.get("trigger_method")
        self.status_code = data.get("status_code")
        self.id_tag_status = data.get("id_tag_status")
        self.expiry_date = data.get("expiry_date")
        self.keyword = data.get("keyword")
        
    
    def to_dict(self):
        return {
            "meta": self.meta.to_dict(),
            "evse": self.evse.to_dict(),
            "data": {
                "transaction_id": self.transaction_id,
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
                "expiry_date": self.expiry_date 
            }
        }


@dataclass(init=False)
class ReservationPayload:
    meta: KafkaMeta
    evse: KafkaEVSE

    connector_id: Optional[str] = None
    expiry_date: Optional[str] = None
    id_tag: Optional[str] = None
    reservation_id: Optional[int] = None

    def __init__(self, **kwargs):
        self.meta = KafkaMeta(**kwargs.get("meta", {}))
        self.evse = KafkaEVSE(**kwargs.get("evse", {}))
        self.connector_id = kwargs.get("data", {}).get("connector_id")
        self.expiry_date = kwargs.get("data", {}).get("expiry_date")
        self.id_tag = kwargs.get("data", {}).get("id_tag")
        self.reservation_id = kwargs.get("data", {}).get("reservation_id")

    def to_dict(self):
        return {
            "meta": self.meta.to_dict(),
            "evse": self.evse.to_dict(),
            "data": {
                "reservation_id": self.reservation_id,
                "connector_id": self.connector_id,
                "expiry_date": self.expiry_date,
                "id_tag": self.id_tag
            }
        }


@dataclass(init=False)
class StartTransactionPayload:
    meta: KafkaMeta
    evse: KafkaEVSE

    transaction_id: Optional[str] = None
    status: Optional[str] = None
    parent_id_tag: Optional[str] = None

    def __init__(self, **kwargs):
        self.meta = KafkaMeta(**kwargs.get("meta", {}))
        self.evse = KafkaEVSE(**kwargs.get("evse", {}))
        self.transaction_id = kwargs.get("data", {}).get("transaction_id")
        self.status = kwargs.get("data", {}).get("status")
        self.parent_id_tag = kwargs.get("data", {}).get("parent_id_tag")

    def to_dict(self):
        return {
            "meta": self.meta.to_dict(),
            "evse": self.evse.to_dict(),
            "data":{   
                "transaction_id": self.transaction_id,
                "id_tag_info": {
                    "status": self.status,
                    "parent_id_tag": self.parent_id_tag,
                }
            }
        }


@dataclass(init=False)
class RemoteStartPayload:
    meta: KafkaMeta
    evse: KafkaEVSE

    connector_id: Optional[str] = None
    id_tag: Optional[str] = None

    def __init__(self, **kwargs):
        self.meta = KafkaMeta(**kwargs.get("meta", {}))
        self.evse = KafkaEVSE(**kwargs.get("evse", {}))
        self.connector_id = kwargs.get("data", {}).get("connector_id")
        self.id_tag = kwargs.get("data", {}).get("id_tag")

    def to_dict(self):
        return {
            "meta": self.meta.to_dict(),
            "evse": self.evse.to_dict(),
            "data": {
                "connector_id": self.connector_id,
                "id_tag": self.id_tag
            }
        }

@dataclass(init=False)
class StopTransactionPayload:
    meta: KafkaMeta
    evse: KafkaEVSE


    transaction_id: Optional[str] = None

    def __init__(self, **kwargs):
        self.meta = KafkaMeta(**kwargs.get("meta", {}))
        self.evse = KafkaEVSE(**kwargs.get("evse", {}))
        data = kwargs.get("data", {})
        self.transaction_id = data.get("transaction_id")
    
    def to_dict(self):
        return {
            "meta": self.meta.to_dict(),
            "evse": self.evse.to_dict(),
            "data": {
                "transaction_id": self.transaction_id,
            }
        }


@dataclass(init=False)
class ListOrderModel:
    keyword: Optional[str] = None
    ev_driver_id: Optional[str] = None
    transaction_id: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None

    def __init__(self, **kwargs):
        self.keyword = kwargs.get("keyword")
        self.ev_driver_id = kwargs.get("ev_driver_id")
        self.transaction_id = kwargs.get("transaction_id")
        self.tenant_id = kwargs.get("tenant_id")
        self.role = kwargs.get("role")


@dataclass(init=False)
class ListOrderResponseModel:

    transaction_id: Optional[str] = None
    status: Optional[str] = None
    charge_point_id: Optional[str] = None
    connector_id: Optional[str] = None
    ev_driver_id: Optional[str] = None
    is_charging: Optional[bool] = None
    is_reservation: Optional[bool] = None
    requires_payment: Optional[bool] = None
    paid_by: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[str] = None
    charged_energy: Optional[str] = None
    amount: Optional[str] = None
    transaction_detail: Optional[str] = None

    def __init__(self, **kwargs):
        self.transaction_id = kwargs.get("transaction_id")
        self.status = kwargs.get("status")
        self.charge_point_id = kwargs.get("charge_point_id")
        self.connector_id = kwargs.get("connector_id")
        self.ev_driver_id = kwargs.get("ev_driver_id")
        self.is_charging = kwargs.get("is_charging")
        self.is_reservation = kwargs.get("is_reservation")
        self.requires_payment = kwargs.get("requires_payment")
        self.paid_by = kwargs.get("paid_by")
        self.start_time = kwargs.get("start_time")
        self.end_time = kwargs.get("end_time")
        self.duration = kwargs.get("duration")
        self.charged_energy = kwargs.get("charged_energy")
        self.amount = kwargs.get("amount")
        self.transaction_detail = kwargs.get("transaction_detail")

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "status": self.status,
            "charge_point_id": self.charge_point_id,
            "connector_id": self.connector_id,
            "ev_driver_id": self.ev_driver_id,
            "is_charging": self.is_charging,
            "is_reservation": self.is_reservation,
            "requires_payment": self.requires_payment,
            "paid_by": self.paid_by,
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
            "duration": self.duration,
            "charged_energy": self.charged_energy,
            "amount": float(self.amount),
            "transaction_detail": self.transaction_detail
        }
    
    def search_keyword(self, keyword: str) -> bool:
        if keyword is None:
            return True
        return any([keyword.lower() in str(v).lower() for k, v in self.to_dict().items() if v is not None])