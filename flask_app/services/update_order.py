import uuid
from flask_app.database_sessions import Database
from flask_app.services.common_function import DataValidation
from flask_app.services.create_order import CreateOrder
from ms_tools.kafka_management.kafka_topic import Topic,KafkaMessage
from microservice_utils.settings import logger
from ms_tools.kafka_management.topics import MsCSMSManagement,MsEVSEManagement,MsPaymentManagement,MsEvDriverManagement
from sqlalchemy_.ms_order_service.enum_types import OrderStatus, ReturnActionStatus, ReturnStatus,ProducerTypes,TriggerMethod
from sqlalchemy_.ms_order_service.order import Order
from sqlalchemy_.ms_order_service.transaction import Transaction
from typing import Tuple
from datetime import datetime

class UpdateOrder:
    def __init__(self):
        self.database = Database()
        self.session = self.database.init_session()
        self.data_validation = DataValidation()
    
    def validate_data(self,transaction_id) -> bool:
        try:
            order_exist = self.session.query(Order).filter(Order.transaction_id == transaction_id).first()
            if not order_exist:
                return False
            return order_exist
        except Exception as e:
            logger.error(e)
            return False,str(e)
        finally:
            self.session.close()          
    
    def update_order(self,data,cancel_ind):
        try:
            logger.info(f"#############################################")
            logger.info(f"Updating order: {data}")
            
            producer = data.get("meta").get("producer")
            request_id=data.get("meta").get("request_id")
            transaction_id = data.get("data").get("transaction_id")
            charge_point_id = data.get("data").get("charge_point_id")
            connector_id = data.get("data").get("connector_id")
            id_tag = data.get("data").get("id_tag")
            is_charging = data.get("data").get("is_charging")
            is_reservation = data.get("data").get("is_reservation")
            requires_payment = data.get("data").get("requires_payment")
            tenant_id = data.get("data").get("tenant_id")
            trigger_method = data.get("data").get("trigger_method")
            status_code = data.get("data").get("status_code")

            order_exist = self.validate_data(transaction_id)

            logger.info(f"Order exist: {order_exist}")

            if not isinstance(order_exist,Order):
                create_order = CreateOrder()
                order_exist = create_order.create_order_rfid(data = data)
                return

            if isinstance(order_exist,Order):
                old_status = order_exist.status

                charging_ind = None
                reservation_ind = None
                order_status = None

                logger.info(f"Order status: {order_exist.status}")

                if status_code in (200,201):
                    if (
                        trigger_method == TriggerMethod.START_TRANSACTION.value and order_exist.status in (OrderStatus.RESERVING.value,OrderStatus.AUTHORIZED.value,OrderStatus.CREATED.value)
                    ):
                        order_status = OrderStatus.CHARGING.value
                        charging_ind=True
                    elif trigger_method == TriggerMethod.MAKE_RESERVATION.value and order_exist.status in (OrderStatus.AUTHORIZED.value,OrderStatus.CREATED.value):
                        order_status = OrderStatus.RESERVING.value
                        reservation_ind=True
                    elif(trigger_method in (TriggerMethod.REMOTE_START.value,TriggerMethod.MAKE_RESERVATION.value,TriggerMethod.AUTHORIZE.value,TriggerMethod.START_TRANSACTION.value) and order_exist.status == OrderStatus.CREATED.value):
                        order_status = OrderStatus.AUTHORIZED.value
                else:
                    if order_exist.status == OrderStatus.CREATED.value:
                        order_status = OrderStatus.AUTHORIZEDFAILED.value
                        if trigger_method == TriggerMethod.MAKE_RESERVATION.value:
                            reservation_ind = False
                        elif trigger_method in (TriggerMethod.REMOTE_START.value,TriggerMethod.START_TRANSACTION.value):
                            charging_ind = False
                
                if cancel_ind == True:
                    order_status = OrderStatus.CANCELLED.value
                    charging_ind = False
                    reservation_ind = False

                logger.info(f"Order status: {order_status}")
                logger.info(f"Charging ind: {charging_ind}")
                logger.info(f"Reservation ind: {reservation_ind}")

                self.session.query(Order).filter(Order.transaction_id==order_exist.transaction_id).update({
                    "charge_point_id": charge_point_id,
                    "connector_id": connector_id,
                    "ev_driver_id": id_tag,
                    "is_charging": is_charging,
                    "is_reservation": is_reservation,
                    "requires_payment": requires_payment,
                    "tenant_id": tenant_id,
                    "status": order_status,
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                order_exist = self.session.query(Order).filter(Order.transaction_id == order_exist.transaction_id).first()

                self.session.query(Transaction).filter(Transaction.transaction_id == transaction_id).update({
                    "transaction_detail": f"{trigger_method} Initated. Order status updated from {old_status} to {order_exist.status}",
                })
                self.session.commit()

                data["data"].update(
                    {
                        "is_reservation":charging_ind,
                        "is_charging":reservation_ind,
                    }
                )

                logger.info(f"producer: {producer}")
                logger.info(f"trigger_method: {trigger_method}")
                logger.info(f"order_status: {order_status}")
                logger.info(f"data: {data}")

                kafka_topic = None

                data["meta"].update(
                    {
                        "producer":ProducerTypes.ORDER_SERVICE.value,
                        "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "version":"1.0.0",
                    }
                )

                if trigger_method == TriggerMethod.AUTHORIZE.value:
                    if order_status in (OrderStatus.AUTHORIZED.value,OrderStatus.AUTHORIZEDFAILED.value):
                        if producer == ProducerTypes.EVSE_AS_SERVICE.value:
                            kafka_topic = MsEVSEManagement.AuthorizeResponse.value
                        if producer == ProducerTypes.OCPP_AS_SERVICE.value:
                            kafka_topic = MsCSMSManagement.AuthorizeResponse.value
                if trigger_method == TriggerMethod.REMOTE_START.value:
                        data["data"] = {
                                    "connector_id": connector_id,
                                    "id_tag": id_tag,
                        }
                        if producer == ProducerTypes.EVSE_AS_SERVICE.value:
                            kafka_topic = MsEVSEManagement.RemoteControlResponse.value
                        if producer == ProducerTypes.OCPP_AS_SERVICE.value:
                            kafka_topic = MsCSMSManagement.ReservationRequest.value
                elif trigger_method == TriggerMethod.MAKE_RESERVATION.value:
                        if producer == ProducerTypes.EVSE_AS_SERVICE.value:
                            kafka_topic = MsEVSEManagement.ReservationResponse.value
                        if producer == ProducerTypes.OCPP_AS_SERVICE.value:
                            if reservation_ind == True:
                                data["data"] = {
                                    "reservation_id": transaction_id,
                                    "connector_id": connector_id,
                                    "expiry_date": data.get("data").get("expiry_date"),
                                    "id_tag": id_tag,
                                }

                                kafka_topic = MsCSMSManagement.ReservationResponse.value
                elif trigger_method == TriggerMethod.START_TRANSACTION.value:
                        if producer == ProducerTypes.EVSE_AS_SERVICE.value:
                            kafka_topic = MsEVSEManagement.RemoteControlResponse.value
                        if producer == ProducerTypes.OCPP_AS_SERVICE.value:
                            if 'error_description' in data["data"]:
                                id_tag_status = data.get("data").get("error_description").get("id_tag_status")
                            else: 
                                id_tag_status = data.get("data").get("id_tag_status")
                            data["data"] = {
                                "transaction_id": transaction_id,
                                "id_tag_info": {
                                    "status": id_tag_status,
                                    "parent_id_tag": data.get("data").get("id_tag"),
                                    "expiry_date": data.get("data").get("expiry_date")
                                }
                            }
                            kafka_topic = MsCSMSManagement.RemoteControlResponse.value
                elif order_status == OrderStatus.CANCELLED.value:
                    if requires_payment == True:
                        kafka_topic = MsPaymentManagement.CancelPaymentRequest.value
                
                logger.info(f"Kafka topic: {kafka_topic}")

                if kafka_topic is not None:
                    kafka_out(topic= kafka_topic,data=data,request_id=request_id)
        except Exception as e:
            logger.error(f"(X) Error while updating order: {e}")
            self.session.rollback()
            return {"message": "update order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()

def kafka_out(topic: str, data: dict, request_id: str):
    from kafka_app.main import kafka_app

    logger.info("###################")
    logger.info(f"KAFKA OUT: {data}")

    kafka_app.send(
        topic=Topic(
            name=topic,
            data=data,
        ),
        request_id=request_id
    )


