import uuid
from flask_app.database_sessions import Database
from flask_app.services.common_function import DataValidation
from flask_app.services.models import KafkaPayload,ReservationPayload, StartTransactionPayload
from kafka_app.kafka_management.kafka_topic import Topic,KafkaMessage
from microservice_utils.settings import logger
from kafka_app.kafka_management.topic_enum import MsCSMSManagement,MsEVSEManagement,MsPaymentManagement,MsOrderManagement
from sqlalchemy_.ms_order_service.enum_types import OrderStatus, ReturnActionStatus, ReturnStatus,ProducerTypes,TriggerMethod
from sqlalchemy_.ms_order_service.order import Order
from sqlalchemy_.ms_order_service.transaction import Transaction
from typing import Tuple
from datetime import datetime, timedelta
from flask_app.services.common_function import kafka_out

class UpdateOrder:
    def __init__(self):
        self.database = Database()
        self.session = self.database.init_session()
        self.data_validation = DataValidation()        
    
    def update_order(self,data:KafkaPayload,cancel_ind):
        try:
            data.expiry_date = data.expiry_date.isoformat() if data.expiry_date else  (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info("#############################################")
            logger.info(f"Updating order: {data}")

            order_exist = self.data_validation.validate_order(transaction_id=data.transaction_id)
            logger.info(f"order_exist: {order_exist}")
            if order_exist is None:
                order_exist = self.data_validation.validate_order_request(request_id=data.meta.request_id)
                if not isinstance(order_exist,Order) and data.trigger_method == TriggerMethod.START_TRANSACTION.value:
                    from flask_app.services.create_order import CreateOrder
                    create_order = CreateOrder()
                    order_exist = create_order.create_order_rfid(data = data)
            
            if not isinstance(order_exist,Order):
                return

            if isinstance(order_exist,Order):
                old_status = order_exist.status
                logger.info(f"old_status: {old_status}")

                charging_ind = None
                reservation_ind = None
                order_status = None

                transaction_exists = self.data_validation.validate_transaction(transaction_id=order_exist.transaction_id)
                logger.info(f"transaction_exists exist: {transaction_exists}")
                if not isinstance(transaction_exists,Transaction):
                    return

                if data.status_code is None or (data.status_code is not None and data.status_code in (200,201)):
                    if order_exist.status == OrderStatus.CREATED.value:
                        order_status = OrderStatus.AUTHORIZED.value
                        if transaction_exists:
                            order_exist.status = order_status
                            transaction_exists.transaction_detail = transaction_exists.transaction_detail+f"{data.trigger_method} Initated, rfid_status:{data.id_tag_status}, order status updated from {old_status} to {order_status} from {data.meta.meta_type}."
                            logger.info(f"Transaction detail: {transaction_exists.transaction_detail}")
                            self.session.commit()
                            old_status = order_exist.status
                    if (
                        data.trigger_method in (TriggerMethod.START_TRANSACTION.value,TriggerMethod.REMOTE_START.value) and 
                        order_exist.status in (OrderStatus.RESERVING.value,OrderStatus.AUTHORIZED.value)
                    ):
                        order_status = OrderStatus.CHARGING.value
                        charging_ind=True
                        reservation_ind = False
                        if data.trigger_method in (TriggerMethod.START_TRANSACTION.value,TriggerMethod.REMOTE_START.value):
                            transaction_exists.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            self.session.commit()
                    elif data.trigger_method==TriggerMethod.STOP_TRANSACTION.value and order_exist.status in (OrderStatus.CHARGING.value):
                        order_status = OrderStatus.COMPLETED.value
                        charging_ind = False
                        reservation_ind = False
                        transaction_exists.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        duration_in_seconds = (datetime.strptime(transaction_exists.end_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(transaction_exists.start_time, "%Y-%m-%d %H:%M:%S")).total_seconds()
                        transaction_exists.duration = round(duration_in_seconds / 60)
                        self.session.commit()
                    elif data.trigger_method == TriggerMethod.MAKE_RESERVATION.value and order_exist.status in (OrderStatus.AUTHORIZED.value):
                        order_status = OrderStatus.RESERVING.value
                        reservation_ind=True
                else:
                    if order_exist.status in (OrderStatus.CREATED.value):
                        order_status = OrderStatus.AUTHORIZEDFAILED.value
                        if data.trigger_method == TriggerMethod.MAKE_RESERVATION.value:
                            reservation_ind = False
                        elif data.trigger_method in (TriggerMethod.REMOTE_START.value,TriggerMethod.START_TRANSACTION.value):
                            charging_ind = False
                
                if cancel_ind == True:
                    order_status = OrderStatus.CANCELLED.value
                    charging_ind = False
                    reservation_ind = False

                logger.info(f"Charging ind: {charging_ind}")
                logger.info(f"Reservation ind: {reservation_ind}")

                if transaction_exists and order_status != OrderStatus.AUTHORIZED.value:
                    logger.info(f"old_status: {old_status}")
                    logger.info(f"new_status: {order_status}")
                    transaction_exists.transaction_detail = transaction_exists.transaction_detail+f"{data.trigger_method} Initated, driver return rfid_status:{data.id_tag_status}, order status updated from {old_status} to {order_status} from {data.meta.meta_type}."
                    logger.info(f"Transaction detail: {transaction_exists.transaction_detail}")
                
                self.session.query(Order).filter(Order.transaction_id==order_exist.transaction_id).update(
                    {
                        "charge_point_id": data.evse.charge_point_id,
                        "connector_id": data.connector_id,
                        "ev_driver_id": data.id_tag,
                        "is_charging": charging_ind,
                        "is_reservation": reservation_ind,
                        "requires_payment": data.requires_payment,
                        "tenant_id": data.tenant_id,
                        "status": order_status,
                        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                )
                self.session.commit()

                data.is_charging = charging_ind
                data.is_reservation = reservation_ind            

                logger.info(f"producer: {data.meta.producer}")
                logger.info(f"trigger_method: {data.trigger_method}")
                logger.info(f"order_status: {order_status}")

                kafka_topic = None

                if order_status == OrderStatus.CANCELLED.value:
                    if data.requires_payment == True:
                        kafka_topic = MsPaymentManagement.CANCEL_PAYMENT_REQUEST.value
                elif data.trigger_method == TriggerMethod.AUTHORIZE.value or order_status == OrderStatus.AUTHORIZEDFAILED.value:
                    data.meta.meta_type = "AuthorizeResponse"
                    if data.meta.producer == ProducerTypes.EVSE_AS_SERVICE.value:
                        kafka_topic = MsEVSEManagement.AUTHORIZE_RESPONSE.value
                    if data.meta.producer == ProducerTypes.OCPP_AS_SERVICE.value:
                        kafka_topic = MsCSMSManagement.AUTHORIZE_RESPONSE.value
                    logger.info(f"Kafka topic: {kafka_topic}")
                    if order_status == OrderStatus.AUTHORIZEDFAILED.value:
                        if data.trigger_method == TriggerMethod.MAKE_RESERVATION.value:
                            data.meta.meta_type = "CancelReservation"
                        elif data.trigger_method in (TriggerMethod.REMOTE_START.value,TriggerMethod.START_TRANSACTION.value):
                            data.meta.meta_type = "RemoteStopTransaction"
                        data.trigger_method = TriggerMethod.CANCEL_ORDER.value
                        kafka_out(topic= MsOrderManagement.REJECT_ORDER.value,data=data.to_dict(),request_id=data.request_id)
                    logger.info(f"Kafka topic: {kafka_topic}")
                elif data.trigger_method == TriggerMethod.REMOTE_START.value:
                    if data.meta.producer == ProducerTypes.EVSE_AS_SERVICE.value:
                        kafka_topic = MsEVSEManagement.REMOTE_CONTROL_RESPONSE.value
                    if data.meta.producer == ProducerTypes.OCPP_AS_SERVICE.value:
                        kafka_topic = MsCSMSManagement.RESERVATION_REQUEST.value
                        data.meta.meta_type = "RemoteControlResponse"
                        data.connector_id = order_exist.connector_id
                        data.id_tag = order_exist.ev_driver_id
                elif data.trigger_method == TriggerMethod.MAKE_RESERVATION.value and order_status in (OrderStatus.RESERVING.value,OrderStatus.AUTHORIZEDFAILED.value):
                    data.meta.meta_type = "RemoteControlResponse"
                    if data.meta.producer == ProducerTypes.EVSE_AS_SERVICE.value:
                        kafka_topic = MsEVSEManagement.RESERVATION_REQUEST.value
                    if data.meta.producer == ProducerTypes.OCPP_AS_SERVICE.value:
                        if reservation_ind == True:
                            kafka_topic = MsCSMSManagement.RESERVATION_REQUEST.value
                            reservation_payload = ReservationPayload()
                            reservation_payload.meta.request_id = data.meta.request_id
                            reservation_payload.meta.action = 'ReserveNow'
                            reservation_payload.meta.meta_type = data.meta.meta_type
                            reservation_payload.evse.charge_point_id = data.evse.charge_point_id
                            reservation_payload.evse.subprotocol = data.evse.subprotocol
                            reservation_payload.reservation_id = order_exist.transaction_id
                            reservation_payload.connector_id = order_exist.connector_id
                            reservation_payload.expiry_date = data.expiry_date
                            reservation_payload.id_tag = data.id_tag
                            data = reservation_payload
                elif data.trigger_method == TriggerMethod.START_TRANSACTION.value:
                    data.meta.meta_type = "RemoteControlResponse"
                    if data.meta.producer == ProducerTypes.EVSE_AS_SERVICE.value:
                        kafka_topic = MsEVSEManagement.REMOTE_CONTROL_RESPONSE.value
                    if data.meta.producer == ProducerTypes.OCPP_AS_SERVICE.value:
                        kafka_topic = MsCSMSManagement.REMOTE_CONTROL_RESPONSE.value
                        start_transaction_payload = StartTransactionPayload()
                        start_transaction_payload.meta.request_id = data.meta.request_id
                        start_transaction_payload.meta.action = 'RemoteStartTransaction'
                        start_transaction_payload.meta.meta_type = data.meta.meta_type
                        start_transaction_payload.evse.charge_point_id = data.evse.charge_point_id
                        start_transaction_payload.evse.subprotocol = data.evse.subprotocol
                        start_transaction_payload.transaction_id = order_exist.transaction_id
                        start_transaction_payload.status = data.id_tag_status
                        start_transaction_payload.parent_id_tag = data.id_tag
                        start_transaction_payload.expiry_date = data.expiry_date
                        data = start_transaction_payload
                
                data.meta.producer = ProducerTypes.ORDER_SERVICE.value
                data.meta.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data.meta.version = "1.0.0"

                logger.info(f"data: {data.to_dict()}")
                
                logger.info(f"Kafka topic: {kafka_topic}")
                if kafka_topic is not None:
                    kafka_out(topic= kafka_topic,data=data.to_dict(),request_id=data.meta.request_id)
        except Exception as e:
            logger.error(f"(X) Error while updating order: {e}")
            self.session.rollback()
            return {"message": "update order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()




