import uuid
from flask_app.database_sessions import Database
from flask_app.services.common_function import DataValidation
from microservice_utils.settings import logger
from ms_tools.kafka_management.topics import MsCSMSManagement,MsEVSEManagement,MsPaymentManagement
from sqlalchemy_.ms_order_service.enum_types import OrderStatus, ReturnActionStatus, ReturnStatus
from sqlalchemy_.ms_order_service.order import Order
from sqlalchemy_.ms_order_service.transaction import Transaction
from typing import Tuple
from datetime import datetime

class UpdateOrder:
    def init(self):
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
            data = data["meta"].update(
                {
                    "service_name":"ms_order_service",
                    "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version":"1.0.0",
                    "type": "order_update"
                }
            )
            
            request_id=data.get("meta").get("request_id")
            transaction_id = data.get("data").get("transaction_id")
            charge_point_id = data.get("data").get("charge_point_id")
            connector_id = data.get("data").get("connector_id")
            mobile_id = data.get("data").get("mobile_id")
            rfid = data.get("data").get("rfid")
            is_charging = data.get("data").get("is_charging")
            is_reservation = data.get("data").get("is_reservation")
            requires_payment = data.get("data").get("requires_payment")
            tenant = data.get("data").get("tenant")
            trigger_method = data.get("data").get("trigger_method")
            status_code = data.get("data").get("status_code")
            expiry_date = data.get("data").get("expiry_date")

            order_exist = self.validate_data(transaction_id)
            if order_exist == False:
                data.update({
                    "status": "error",
                    "error": "transaction_id not found",
                    "status_code": 400
                })
            
            if isinstance(order_exist,Order):
                if trigger_method=="authorization" and status_code==200 and order_exist.status==None:
                    order_status = OrderStatus.AUTHORIZED.value
                elif trigger_method == "remote_start" and status_code==200 and order_exist.status==None:
                    order_status = OrderStatus.AUTHORIZED.value
                elif trigger_method == "make_reservation" and status_code==200:
                    order_status = OrderStatus.RESERVING.value
                elif trigger_method == "start_transaction" and status_code==200:
                    order_status = OrderStatus.CHARGING.value
                elif trigger_method=="authorization" and status_code in (400,409):
                    order_status = OrderStatus.AUTHORIZEDFAILED.value
                elif trigger_method in ("remote_start","make_reservation","start_transaction") and status_code in (400,409):
                    order_status = OrderStatus.CANCELLED.value
                    
                order_exist.update({
                    "charge_point_id": charge_point_id,
                    "connector_id": connector_id,
                    "driver_id": mobile_id,
                    "rfid": rfid,
                    "is_charging": is_charging,
                    "is_reservation": is_reservation,
                    "requires_payment": requires_payment,
                    "tenant": tenant,
                    "status": order_status,
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.session.commit()

                if order_status == OrderStatus.AUTHORIZEDFAILED.value:
                    if mobile_id is not None:
                        kafka_send(topic=MsEVSEManagement.AuthorizationFailed.value,data=data,request_id=request_id)
                    if rfid is not None:
                        kafka_send(topic=MsCSMSManagement.AuthorizationFailed.value,data=data,request_id=request_id)
                    
                    ###KAFKA OUT TO PAYMENT SERVICE
                    if requires_payment == True:
                        kafka_send(topic=MsPaymentManagement.CancelPaymentRequest.value,data=data,request_id=request_id)
                elif order_status == OrderStatus.AUTHORIZED.value:
                    if mobile_id is not None:
                        kafka_send(topic=MsEVSEManagement.StartTransaction.value,data=data,request_id=request_id)
                    if rfid is not None:
                        kafka_send(topic=MsCSMSManagement.StartTransaction.value,data=data,request_id=request_id)
                elif order_status == OrderStatus.CHARGING.value:
                    if mobile_id is not None:
                        #kafka_send(topic=MsEVSEManagement.RemoteStart.value,data=data,request_id=request_id)
                        pass
                    if rfid is not None:
                        #kafka_send(topic=MsCSMSManagement.RemoteStart.value,data=data,request_id=request_id)
                        pass
                elif order_status == OrderStatus.RESERVING.value:
                    if mobile_id is not None:
                        kafka_send(topic=MsEVSEManagement.MakeReservation.value,data=data,request_id=request_id)
                    if rfid is not None:
                        kafka_send(topic=MsCSMSManagement.MakeReservation.value,data=data,request_id=request_id)
                elif order_status == OrderStatus.CANCELLED.value:
                    if requires_payment == True:
                        kafka_send(topic=MsPaymentManagement.CancelPaymentRequest.value,data=data,request_id=request_id)
        except Exception as e:
            logger.error(f"(X) Error while creating order: {e}")
            self.session.rollback()
            return {"message": "update order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()

async def kafka_send(topic: str, data: dict, request_id: str):
    from kafka_app.main import kafka_app
    from ms_tools.kafka_management.kafka_topic import Topic
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