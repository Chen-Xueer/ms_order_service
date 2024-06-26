import uuid
from flask_app.database_sessions import Database
from flask_app.services.common_function import DataValidation
from flask_app.services.models import KafkaPayload, RemoteStartPayload
from microservice_utils.settings import logger
from kafka_app.kafka_management.topic_enum import MsCSMSManagement, MsEvDriverManagement
from sqlalchemy_.ms_order_service.enum_types import ReturnActionStatus, ReturnStatus, OrderStatus
from sqlalchemy_.ms_order_service.order import Order
from sqlalchemy_.ms_order_service.tenant import Tenant
from sqlalchemy_.ms_order_service.transaction import Transaction
from typing import Tuple
from datetime import datetime
from flask_app.services.common_function import kafka_out

class CreateOrder:
    def __init__(self):
        database = Database()
        self.session = database.init_session()
        self.data_validation = DataValidation()
    
    def db_insert_order(self,**kwargs):
        try:
            tenant_id =  kwargs.get("tenant_id")
            charge_point_id = kwargs.get("charge_point_id")
            connector_id = kwargs.get("connector_id")
            ev_driver_id = kwargs.get("id_tag")
            trigger_method = kwargs.get("trigger_method")
            request_id = kwargs.get("request_id")
            requires_payment = kwargs.get("requires_payment")
            
            if 'start_charging' in trigger_method:
                charging_ind=True
            else:
                charging_ind=False
            
            if 'make_reservation' in trigger_method:
                reservation_ind=True
            else:
                reservation_ind=False

            order_created = Order(
                            tenant_id=tenant_id,
                            status=OrderStatus.CREATED.value,
                            charge_point_id=charge_point_id,
                            connector_id=connector_id,
                            ev_driver_id=ev_driver_id,
                            tariff_id=None,
                            is_charging=charging_ind,
                            is_reservation=reservation_ind,
                            requires_payment=requires_payment,
                            create_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            last_update=None,
                            request_id=request_id,
                        )
            self.session.add(order_created)
            self.session.commit()
            return order_created
        except Exception as e:
            logger.error(f"(X) Error while creating order: {e}")
            self.session.rollback()
            return {"message": "insert order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500

    def db_insert_transaction(self,transaction_id,trans_det):
        try:
            transaction_created = Transaction(
                            transaction_id=transaction_id,
                            amount=None,
                            charged_energy=None,
                            duration=None,
                            paid_by=None,
                            transaction_detail=trans_det
                        )
            self.session.add(transaction_created)
            self.session.commit()
            return transaction_created
        except Exception as e:
            logger.error(f"(X) Error while creating transaction: {e}")
            self.session.rollback()
            return {"message": "insert transaction failed", "action":"transaction_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500

    def remote_start_payload(self,data:KafkaPayload):
        try:
            data.meta.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data.meta.version = "1.0.0"
            data.meta.meta_type = "order_creation"
            data.meta.action = "RemoteStartTransaction"

            remote_start_payload = RemoteStartPayload()
            remote_start_payload.meta.request_id = data.meta.request_id
            remote_start_payload.meta.action = 'RemoteStartTransaction'
            remote_start_payload.meta.meta_type = 'ReservationRequest'
            remote_start_payload.evse.charge_point_id = data.evse.charge_point_id
            remote_start_payload.evse.subprotocol = data.evse.subprotocol
            remote_start_payload.id_tag = data.id_tag
            remote_start_payload.connector_id = data.connector_id
            data = remote_start_payload

            kafka_out(topic=MsCSMSManagement.RESERVATION_REQUEST.value,data=data.to_dict(),request_id=data.meta.request_id)
            
            return data.to_dict()
        except Exception as e:
            logger.error(f"(X) Error while creating order: {e}")
            self.session.rollback()
            return {"message": "create order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        


    def create_order_mobile_id(self,mobile_id,data:KafkaPayload):
        try:
            #tenant_exists = self.data_validation.validate_tenants(tenant_id=tenant_id,action=data.meta.meta_type)
            #if not isinstance(tenant_exists,Tenant):
            #    return tenant_exists
            #logger.info(f"Tenant exists: {tenant_exists}")
            
            data.meta.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data.meta.version = "1.0.0"
            data.meta.meta_type = "order_creation"
            data.meta.action = "RemoteStartTransaction"
            
            order_created = self.db_insert_order(
                charge_point_id=data.evse.charge_point_id,
                connector_id=data.connector_id,
                id_tag=mobile_id,
                trigger_method=data.trigger_method,
                tenant_id=data.tenant_id,
                request_id = data.meta.request_id
            )

            logger.info(f"Order created: {order_created}")

            if not isinstance(order_created,Order):
                return order_created
            
            trans_det = "Order created for remote_start."
            
            transaction_created = self.db_insert_transaction(transaction_id=order_created.transaction_id,trans_det=trans_det)
            if not isinstance(transaction_created,Transaction):
                self.session.query(Order).filter(Order.transaction_id==order_created.transaction_id).delete()
                self.session.commit()
                return transaction_created
            
            logger.info(f"Transaction created: {transaction_created}")
            
            if isinstance(order_created,Order) and isinstance(transaction_created,Transaction):
                data.transaction_id = order_created.transaction_id
                data.id_tag = mobile_id
                data.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data.is_reservation = False
                data.is_charging = False
                data.tenant_id = data.tenant_id
                data.status_code = 201
                
                kafka_out(topic=MsEvDriverManagement.DRIVER_VERIFICATION_REQUEST.value,data=data.to_dict(),request_id=data.meta.request_id)
            
                return data.to_dict()
        except Exception as e:
            logger.error(f"(X) Error while creating order: {e}")
            self.session.rollback()
            return {"message": "create order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()
    
    def create_order_rfid(self,data:KafkaPayload):
        try:
            #tenant_exists = self.data_validation.validate_tenants(tenant_id=data.tenant_id,action=data.meta.meta_type)
            #if not isinstance(tenant_exists,Tenant):
            #    return tenant_exists
            #logger.info(f"Tenant exists: {tenant_exists}")
            data.meta.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data.meta.version = "1.0.0"
            data.meta.meta_type = "order_creation"

            logger.info(f"Creating order for RFID: {data.id_tag}")
            
            order_created = self.db_insert_order(
                charge_point_id=data.evse.charge_point_id,
                connector_id=data.connector_id,
                id_tag=data.id_tag,
                trigger_method=data.trigger_method,
                tenant_id=data.tenant_id,
                request_id = data.meta.request_id
            )
            
            if not isinstance(order_created,Order):
                return order_created

            trans_det = f"Order created for {data.trigger_method}."
            
            transaction_created = self.db_insert_transaction(transaction_id=order_created.transaction_id,trans_det=trans_det)
            if not isinstance(transaction_created,Transaction):
                self.session.query(Order).filter(Order.transaction_id==order_created.transaction_id).delete()
                self.session.commit()
                return transaction_created
            
            logger.info(f"Transaction created: {transaction_created}")
            
            if isinstance(order_created,Order) and isinstance(transaction_created,Transaction):
                data.transaction_id = order_created.transaction_id
                data.connector_id = order_created.connector_id
                data.id_tag = order_created.ev_driver_id
                data.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data.is_reservation = False
                data.is_charging = False
                data.tenant_id = order_created.tenant_id
                data.requires_payment = order_created.requires_payment
                data.status_code = 201

                kafka_out(topic=MsEvDriverManagement.DRIVER_VERIFICATION_REQUEST.value,data=data.to_dict(),request_id=data.meta.request_id)
            
                return data.to_dict()
        except Exception as e:
            logger.error(f"(X) Error while creating order:{e}")
            self.session.rollback()
            return {"message": "create order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()
    