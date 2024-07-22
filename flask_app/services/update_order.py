import uuid

from sqlalchemy import desc
from flask_app.database_sessions import Database
from flask_app.services.common_function import DataValidation
from flask_app.services.models import KafkaPayload, RemoteStartPayload,ReservationPayload, StartTransactionPayload, StopTransactionPayload
from microservice_utils.settings import logger
from kafka_app.kafka_management.topic_enum import MsCSMSManagement,MsEVSEManagement,MsPaymentManagement,MsOrderManagement
from sqlalchemy_.ms_order_service.enum_types import OrderStatus, ReturnActionStatus, ReturnStatus,ProducerTypes,TriggerMethod
from sqlalchemy_.ms_order_service.order import Order
from sqlalchemy_.ms_order_service.transaction import Transaction
from typing import Tuple
from datetime import datetime, timedelta

class UpdateOrder:
    def __init__(self):
        self.database = Database()
        self.session = self.database.init_session()
        self.data_validation = DataValidation()        
    
    def update_order(self,data:KafkaPayload,cancel_ind):
        try:
            data.expiry_date = data.expiry_date if data.expiry_date else  (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info("#################Updating order############################")
            logger.info(f"meta: {data.meta}")
            logger.info(f"action: {data.meta.action}")
            logger.info(f"transaction_id: {data.transaction_id}")

            order_exist = self.data_validation.validate_order(transaction_id=data.transaction_id)
            if order_exist is None:
                order_exist = self.data_validation.validate_order_request(request_id=data.meta.request_id)
                logger.info(f"by request id: {order_exist}")

            if order_exist is None:
                logger.info(f"by ev_driver_id: {data.id_tag}")
                logger.info(f"charge_point_id: {data.evse.charge_point_id}")
                logger.info(f"connector_id: {data.connector_id}")
                order_exist = self.session.query(Order).filter(Order.ev_driver_id == data.id_tag, Order.status==OrderStatus.PREPARECHARGING.value,Order.charge_point_id == data.evse.charge_point_id,Order.connector_id == data.connector_id).order_by(desc(Order.transaction_id)).first()
                logger.info(f"latest transaction: {order_exist}")
                
            if order_exist is None and data.meta.action == TriggerMethod.START_TRANSACTION.value:
                from flask_app.services.create_order import CreateOrder
                create_order = CreateOrder()
                order_exist = create_order.create_order(data = data)
            
            logger.info(f"order_exist: {order_exist}")

            transaction_exists = self.data_validation.validate_transaction(transaction_id=order_exist.transaction_id)
            logger.info(f"transaction_exists details: {transaction_exists.transaction_detail}")

            if order_exist is not None and transaction_exists is not None:
                current_order_status = order_exist.status

                logger.info(f"current order status: {current_order_status}")

                charging_ind = False
                reservation_ind = False
                new_order_status = None
                
                if cancel_ind == True or data.status == 'Rejected':
                    new_order_status = OrderStatus.CANCELLED.value
                else:
                    #### Order Creation Stage ####
                    if order_exist.status == OrderStatus.CREATED.value:
                        logger.info(f"status_code : {data.status_code}")
                        if data.status_code is None or (data.status_code is not None and data.status_code in [200,201]):
                            new_order_status = OrderStatus.AUTHORIZED.value
                        else:
                            new_order_status = OrderStatus.AUTHORIZEDFAILED.value

                        self.session.query(Order).filter(Order.transaction_id == order_exist.transaction_id).update({
                            "status": new_order_status,
                            "is_charging": charging_ind,
                            "is_reservation": reservation_ind,
                        })

                        self.session.query(Transaction).filter(Transaction.transaction_id == order_exist.transaction_id).update({"transaction_detail": transaction_exists.transaction_detail + f"{data.meta.action} Initated, id_tag_status:{data.id_tag_status}, order status updated from {current_order_status} to {new_order_status} from {data.meta.meta_type}."})
                        self.session.commit()

                        order_exist = self.session.query(Order).filter(Order.transaction_id == order_exist.transaction_id).first()
                        transaction_exists = self.session.query(Transaction).filter(Transaction.transaction_id == order_exist.transaction_id).first()

                        logger.info(f"updated order_exist status: {order_exist.status}")

                    #### Order Already Authorized Stage ####
                    if order_exist.status == OrderStatus.AUTHORIZED.value:
                        if data.meta.action == TriggerMethod.MAKE_RESERVATION.value:
                            new_order_status = OrderStatus.RESERVING.value
                            reservation_ind=True
                        
                        if data.meta.action == TriggerMethod.REMOTE_START.value:
                            new_order_status = OrderStatus.PREPARECHARGING.value

                        if data.meta.action == TriggerMethod.START_TRANSACTION.value:
                            new_order_status = OrderStatus.CHARGING.value
                            charging_ind=True
                       
                    elif order_exist.status == OrderStatus.RESERVING.value:
                        if data.meta.action == TriggerMethod.REMOTE_START.value:
                            new_order_status = OrderStatus.PREPARECHARGING.value

                        if data.meta.action == TriggerMethod.START_TRANSACTION.value:
                            new_order_status = OrderStatus.CHARGING.value
                            charging_ind=True
                    
                    elif order_exist.status == OrderStatus.PREPARECHARGING.value:
                        if data.meta.action == TriggerMethod.START_TRANSACTION.value:
                            new_order_status = OrderStatus.CHARGING.value
                            charging_ind=True

                    elif order_exist.status == OrderStatus.CHARGING.value:
                        if data.meta.action==TriggerMethod.STOP_TRANSACTION.value:
                            new_order_status = OrderStatus.COMPLETED.value

                logger.info(f"Charging ind: {charging_ind}")
                logger.info(f"Reservation ind: {reservation_ind}")

                if transaction_exists and new_order_status not in [OrderStatus.AUTHORIZED.value,OrderStatus.AUTHORIZEDFAILED.value]:
                    logger.info(f"after_authorization_status: {current_order_status}")
                    logger.info(f"latest_status: {new_order_status}")
                    transaction_update_fields={}
                    
                    if new_order_status == OrderStatus.COMPLETED.value:
                        transaction_update_fields["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        transaction_update_fields["duration"] = round((datetime.now() - transaction_exists.start_time).total_seconds() / 60)
                        #### NEED CALCULATION FOR TOTAL COST FROM TARIFF MANAGEMENT ####
                        transaction_update_fields["transaction_detail"] = transaction_exists.transaction_detail + f"Order Completed, order status updated from {current_order_status} to {new_order_status} from {data.meta.meta_type}."
                    else:
                        if new_order_status == OrderStatus.CHARGING.value:
                            transaction_update_fields["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        transaction_update_fields["transaction_detail"] = transaction_exists.transaction_detail + f"order status updated from {current_order_status} to {new_order_status} from {data.meta.meta_type}."

                    if len(transaction_update_fields) > 0:
                        logger.info(f"transaction_update_fields: {transaction_update_fields}")
                        self.session.query(Transaction).filter(Transaction.transaction_id == order_exist.transaction_id).update(transaction_update_fields)
                        self.session.commit()

                order_update_fields={
                    "status": new_order_status,
                    "is_charging": charging_ind,
                    "is_reservation": reservation_ind,
                }
                if data.evse.charge_point_id is not None:
                    order_update_fields["charge_point_id"] = data.evse.charge_point_id
                if data.connector_id is not None:
                    order_update_fields["connector_id"] = data.connector_id
                if data.id_tag is not None:
                    order_update_fields["ev_driver_id"] = data.id_tag
                if data.tenant_id is not None:
                    order_update_fields["tenant_id"] = data.tenant_id
                if data.requires_payment is not None:
                    order_update_fields["requires_payment"] = data.requires_payment
                                    
                logger.info(f"order_update_fields: {order_update_fields}")

                if len(order_update_fields) > 0:
                    logger.info(f"update order: {order_exist.transaction_id}")
                    self.session.query(Order).filter(Order.transaction_id == order_exist.transaction_id).update(order_update_fields)
                    self.session.commit()
                    logger.info(f"order updated status: {order_exist.status}")
                logger.info(f"order updated status: {order_exist.status}")
                data.is_charging = charging_ind
                data.is_reservation = reservation_ind            

                logger.info(f"producer: {data.meta.producer}")
                logger.info(f"action: {data.meta.action}")
                logger.info(f"order_status: {new_order_status}")

                kafka_topic = None

                if new_order_status == OrderStatus.CANCELLED.value:
                    if data.requires_payment == True:
                        kafka_topic = MsPaymentManagement.CANCEL_PAYMENT_REQUEST.value
                    
                    kafka_out(topic= MsOrderManagement.REJECT_ORDER_SUCCESS.value,data=data.to_dict(),request_id=data.meta.request_id)
                
                elif data.meta.action in TriggerMethod.AUTHORIZE.value or new_order_status == OrderStatus.AUTHORIZEDFAILED.value:
                    if new_order_status == OrderStatus.AUTHORIZEDFAILED.value:
                        if data.meta.action == TriggerMethod.MAKE_RESERVATION.value:
                            data.meta.meta_type = "CancelReservation"
                        elif data.meta.action in (TriggerMethod.REMOTE_START.value,TriggerMethod.START_TRANSACTION.value):
                            data.meta.meta_type = "RemoteStopTransaction"
                        data.meta.action = TriggerMethod.CANCEL_ORDER.value
                        kafka_out(topic= MsOrderManagement.REJECT_ORDER.value,data=data.to_dict(),request_id=data.meta.request_id)
                    logger.info(f"Kafka topic: {kafka_topic}")

                    data.meta.meta_type = "AuthorizeResponse"
                    if data.meta.producer == ProducerTypes.EVSE_AS_SERVICE.value:
                        kafka_topic = MsEVSEManagement.AUTHORIZE_RESPONSE.value
                    if data.meta.producer == ProducerTypes.OCPP_AS_SERVICE.value:
                        kafka_topic = MsCSMSManagement.AUTHORIZE_RESPONSE.value
                    logger.info(f"Kafka topic: {kafka_topic}")

                elif data.meta.action == TriggerMethod.REMOTE_START.value:
                    if data.meta.producer == ProducerTypes.CHARGER_MGMT.value:
                        kafka_topic = MsCSMSManagement.RESERVATION_REQUEST.value
                        data.meta.meta_type = MsCSMSManagement.RESERVATION_REQUEST.value
                        remote_start_payload = RemoteStartPayload()
                        remote_start_payload.meta.producer = data.meta.producer
                        remote_start_payload.meta.request_id = data.meta.request_id
                        remote_start_payload.meta.tenant_id = data.tenant_id
                        remote_start_payload.meta.action = TriggerMethod.REMOTE_START.value
                        remote_start_payload.meta.meta_type = MsCSMSManagement.RESERVATION_REQUEST.value
                        remote_start_payload.evse.charge_point_id = data.evse.charge_point_id
                        remote_start_payload.evse.subprotocol = data.evse.subprotocol
                        remote_start_payload.id_tag = data.id_tag
                        remote_start_payload.connector_id = data.connector_id
                        data = remote_start_payload
                    
                    if data.meta.producer == ProducerTypes.CSMS_AS_SERVICE.value:
                        kafka_topic = MsCSMSManagement.REMOTE_CONTROL_RESPONSE.value
                        start_transaction_payload = StartTransactionPayload()
                        start_transaction_payload.meta.request_id = data.meta.request_id
                        start_transaction_payload.meta.action = TriggerMethod.REMOTE_START.value
                        start_transaction_payload.meta.meta_type = MsCSMSManagement.REMOTE_CONTROL_RESPONSE.value
                        start_transaction_payload.evse.charge_point_id = data.evse.charge_point_id
                        start_transaction_payload.evse.subprotocol = data.evse.subprotocol
                        start_transaction_payload.transaction_id = order_exist.transaction_id
                        start_transaction_payload.status = data.status
                        start_transaction_payload.parent_id_tag = order_exist.ev_driver_id
                        data = start_transaction_payload
                        
                elif data.meta.action == TriggerMethod.MAKE_RESERVATION.value and new_order_status in [OrderStatus.RESERVING.value,OrderStatus.AUTHORIZEDFAILED.value]:
                    data.meta.meta_type = "RemoteControlResponse"
                    if data.meta.producer == ProducerTypes.EVSE_AS_SERVICE.value:
                        kafka_topic = MsEVSEManagement.RESERVATION_REQUEST.value
                    if data.meta.producer == ProducerTypes.OCPP_AS_SERVICE.value:
                        if reservation_ind == True:
                            kafka_topic = MsCSMSManagement.RESERVATION_REQUEST.value
                            reservation_payload = ReservationPayload()
                            reservation_payload.meta.request_id = data.meta.request_id
                            reservation_payload.meta.action = TriggerMethod.MAKE_RESERVATION.value
                            reservation_payload.meta.meta_type = MsCSMSManagement.RESERVATION_REQUEST.valuez
                            reservation_payload.evse.charge_point_id = data.evse.charge_point_id
                            reservation_payload.evse.subprotocol = data.evse.subprotocol
                            reservation_payload.reservation_id = order_exist.transaction_id
                            reservation_payload.connector_id = order_exist.connector_id
                            reservation_payload.expiry_date = data.expiry_date
                            reservation_payload.id_tag = order_exist.ev_driver_id
                            data = reservation_payload

                elif data.meta.action == TriggerMethod.START_TRANSACTION.value:
                    data.meta.meta_type = "RemoteControlResponse"
                    if data.meta.producer == ProducerTypes.OCPP_AS_SERVICE.value:
                        if data.id_tag_status is None and charging_ind == True:
                            data.id_tag_status = "Accepted"
                        kafka_topic = MsCSMSManagement.REMOTE_CONTROL_RESPONSE.value
                        start_transaction_payload = StartTransactionPayload()
                        start_transaction_payload.meta.request_id = data.meta.request_id
                        start_transaction_payload.meta.action = TriggerMethod.START_TRANSACTION.value
                        start_transaction_payload.meta.meta_type = MsCSMSManagement.REMOTE_CONTROL_RESPONSE.value
                        start_transaction_payload.evse.charge_point_id = data.evse.charge_point_id
                        start_transaction_payload.evse.subprotocol = data.evse.subprotocol
                        start_transaction_payload.transaction_id = order_exist.transaction_id
                        start_transaction_payload.status = data.id_tag_status
                        start_transaction_payload.parent_id_tag = order_exist.ev_driver_id
                        #start_transaction_payload.expiry_date = data.expiry_date
                        data = start_transaction_payload
                    
                        kafka_out(topic= MsOrderManagement.CREATE_ORDER_RESPONSE.value,data=data.to_dict(),request_id=data.meta.request_id)

                elif data.meta.action == TriggerMethod.STOP_TRANSACTION.value:
                    data.meta.meta_type = "RemoteStopTransaction"
                    stop_transaction_payload = StopTransactionPayload()
                    stop_transaction_payload.meta.request_id = data.meta.request_id
                    stop_transaction_payload.meta.action = 'RemoteStopTransaction'
                    stop_transaction_payload.meta.meta_type = 'ReservationRequest'
                    stop_transaction_payload.evse.charge_point_id = data.evse.charge_point_id
                    stop_transaction_payload.evse.subprotocol = data.evse.subprotocol
                    stop_transaction_payload.transaction_id = order_exist.transaction_id
                    
                    if data.meta.producer == ProducerTypes.EVSE_AS_SERVICE.value:
                        kafka_topic = MsEVSEManagement.REMOTE_CONTROL_REQUEST.value
                    if data.meta.producer == ProducerTypes.OCPP_AS_SERVICE.value:
                        kafka_topic = MsCSMSManagement.REMOTE_CONTROL_REQUEST.value
                
                data.meta.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data.meta.version = "1.0.0"

                logger.info(f"data: {data.to_dict()}")
                
                logger.info(f"Kafka topic: {kafka_topic}")
                if kafka_topic is not None:
                    kafka_out(topic= kafka_topic,data=data.to_dict(),request_id=data.meta.request_id)
                    #kafka_out(topic= MsOrderManagement.CREATE_ORDER_RESPONSE.value,data=data.to_dict(),request_id=data.meta.request_id)

        except Exception as e:
            logger.error(f"(X) Error while updating order: {e}")
            self.session.rollback()
            return {"message": "update order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()



def kafka_out(topic: str, data: dict, request_id: str):
    from kafka_app.main import kafka_app
    from kafka_app.kafka_management.kafka_topic import Topic
    logger.info("###################")
    logger.info(f"KAFKA OUT: {data}")

    try:
        kafka_app.send(
            topic=Topic(
                name=topic,
                data=data,
            ),
            request_id=request_id
        )
    except Exception as e:
        print(f"Error publishing message to Kafka broker: {e}")


