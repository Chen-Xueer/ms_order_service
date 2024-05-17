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
    
    def update_order(self,data):
        try:
            logger.info(f"#############################################")
            logger.info(f"Updating order: {data}")

            data["meta"].update(
                {
                    "service_name":ProducerTypes.ORDER_SERVICE.value,
                    "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version":"1.0.0",
                    "type": "order_update"
                }
            )
            
            service_name = data.get("meta").get("service_name")
            request_id=data.get("meta").get("request_id")
            transaction_id = data.get("data").get("transaction_id")
            charge_point_id = data.get("data").get("charge_point_id")
            connector_id = data.get("data").get("connector_id")
            id_tag = data.get("data").get("id_tag")
            mobile_id = data.get("data").get("mobile_id")
            rfid = data.get("data").get("rfid")
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

                if status_code in (200,201):
                    if( trigger_method in (TriggerMethod.REMOTE_START.value,TriggerMethod.MAKE_RESERVATION.value,TriggerMethod.AUTHORIZE.value,TriggerMethod.START_TRANSACTION.value) and order_exist.status == OrderStatus.CREATED.value):
                        order_status = OrderStatus.AUTHORIZED.value
                    elif (
                        trigger_method == TriggerMethod.START_TRANSACTION.value and order_exist.status in (OrderStatus.RESERVING.value,OrderStatus.AUTHORIZED.value)
                    ):
                        order_status = OrderStatus.CHARGING.value
                        charging_ind=True
                    elif trigger_method == TriggerMethod.MAKE_RESERVATION.value and order_exist.status == OrderStatus.AUTHORIZED.value:
                        order_status = OrderStatus.RESERVING.value
                        reservation_ind=True
                else:
                    if trigger_method in (TriggerMethod.START_TRANSACTION.value):
                        order_status = OrderStatus.CANCELLED.value
                        charging_ind = False
                    elif (trigger_method in (TriggerMethod.REMOTE_START.value,TriggerMethod.MAKE_RESERVATION.value,TriggerMethod.AUTHORIZE.value) and order_exist.status == OrderStatus.CREATED.value):
                        order_status = OrderStatus.AUTHORIZEDFAILED.value
                        if trigger_method == TriggerMethod.MAKE_RESERVATION.value:
                            reservation_ind = False
                        elif trigger_method == TriggerMethod.REMOTE_START.value:
                            charging_ind = False

                logger.info(f"Order status: {order_status}")

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
                        "id_tag_status": order_status,
                    }
                )

                logger.info(f"service_name: {service_name}")

                if trigger_method in (TriggerMethod.AUTHORIZE.value):
                    if service_name == ProducerTypes.EVSE_AS_SERVICE.value:
                        kafka_out(topic=MsEVSEManagement.AuthorizeResponse.value,data=data,request_id=request_id)
                    if service_name == ProducerTypes.OCPP_AS_SERVICE.value:
                        kafka_out(topic=MsCSMSManagement.AuthorizeResponse.value,data=data,request_id=request_id)
                    
                    if order_status == OrderStatus.AUTHORIZEDFAILED.value:
                        if requires_payment == True:
                            kafka_out(topic=MsPaymentManagement.CancelPaymentRequest.value,data=data,request_id=request_id)

                    elif trigger_method == TriggerMethod.MAKE_RESERVATION.value:
                        kafka_out(topic=MsEVSEManagement.MakeReservation.value,data=data,request_id=request_id)
                    elif trigger_method in (TriggerMethod.START_TRANSACTION.value,TriggerMethod.REMOTE_START.value):
                        kafka_out(topic=MsEvDriverManagement.DriverVerificationResponse.value,data=data,request_id=request_id)
                #elif order_status in OrderStatus.CHARGING.value:
                #    if service_name == ProducerTypes.EVSE_AS_SERVICE.value:
                #        kafka_send(topic=MsEVSEManagement.StartTransaction.value,data=data,request_id=request_id)
                #    if service_name == ProducerTypes.OCPP_AS_SERVICE.value:
                #        kafka_send(topic=MsCSMSManagement.StartTransaction.value,data=data,request_id=request_id)
                #    kafka_send(topic=MsEvDriverManagement.UpdateDriverStatus.value,data=data,request_id=request_id)
                #elif order_status == OrderStatus.RESERVING.value:
                #    if service_name == ProducerTypes.EVSE_AS_SERVICE.value:
                #        kafka_send(topic=MsEVSEManagement.MakeReservation.value,data=data,request_id=request_id)
                #    if service_name == ProducerTypes.OCPP_AS_SERVICE.value:
                #        kafka_send(topic=MsCSMSManagement.MakeReservation.value,data=data,request_id=request_id)
                #    kafka_send(topic=MsEvDriverManagement.UpdateDriverStatus.value,data=data,request_id=request_id)
                #elif order_status == OrderStatus.CANCELLED.value:
                #    if requires_payment == True:
                #        kafka_send(topic=MsPaymentManagement.CancelPaymentRequest.value,data=data,request_id=request_id)
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


