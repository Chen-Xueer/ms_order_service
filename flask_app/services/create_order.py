import uuid
from flask_app.database_sessions import Database
from flask_app.services.common_function import DataValidation
from microservice_utils.settings import logger
from ms_tools.kafka_management.topics import MsEvDriverManagement, MsPaymentManagement
from sqlalchemy_.ms_order_service.enum_types import ReturnActionStatus, ReturnStatus, OrderStatus
from sqlalchemy_.ms_order_service.order import Order
from sqlalchemy_.ms_order_service.transaction import Transaction
from typing import Tuple
from datetime import datetime

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
                            requires_payment=False,
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


    def create_order_mobile_id(self,mobile_id,data,tenant_id):
        try:
            request_id = data.get("meta").get("request_id")

            data["meta"].update(
                {
                    "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version":"1.0.0",
                    "type": "order_creation",
                    "action": "RemoteStartTransaction"
                }
            )
        
            charge_point_id = data.get("data").get("charge_point_id")
            connector_id = data.get("data").get("connector_id")
            
            order_created = self.db_insert_order(
                charge_point_id=charge_point_id,
                connector_id=connector_id,
                id_tag=mobile_id,
                trigger_method='remote_start',
                tenant_id=tenant_id,
                request_id = request_id
            )

            logger.info(f"Order created: {order_created}")

            if not isinstance(order_created,Order):
                return order_created
            
            trans_det = "Order created for remote_start"
            
            transaction_created = self.db_insert_transaction(transaction_id=order_created.transaction_id,trans_det=trans_det)
            if not isinstance(transaction_created,Transaction):
                self.session.query(Order).filter(Order.transaction_id==order_created.transaction_id).delete()
                self.session.commit()
                return transaction_created
            
            logger.info(f"Transaction created: {transaction_created}")
            
            if isinstance(order_created,Order) and isinstance(transaction_created,Transaction):
                data["data"].update(
                    {
                        "transaction_id": order_created.transaction_id,
                        "charge_point_id": charge_point_id,
                        "connector_id": connector_id,
                        "id_tag": mobile_id,
                        "trigger_method": 'remote_start',
                        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "is_reservation": False,
                        "is_charging": False,
                        "tenant_id": tenant_id,
                        "requires_payment": False,
                        "status_code": 201,
                    }
                )
                kafka_send(topic=MsEvDriverManagement.DriverVerificationRequest.value,data=data,request_id=request_id)

        except Exception as e:
            logger.error(f"(X) Error while creating order: {e}")
            self.session.rollback()
            return {"message": "create order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()
    
    def create_order_rfid(self,data):
        data["meta"].update(
            {
                "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version":"1.0.0",
                "type": "order_creation"
            }
        )

        try:
            id_tag = data.get("data").get("id_tag")
            tenant_id = data.get("data").get("tenant_id")
            charge_point_id = data.get("evse").get("charge_point_id")
            connector_id = data.get("data").get("connector_id")
            trigger_method = data.get("data").get("trigger_method")
            request_id = data.get("meta").get("request_id")
            requires_payment = data.get("data").get("requires_payment")
            start_time = data.get("data").get("start_time")
            
            logger.info(f"Creating order for RFID: {id_tag}")
            
            order_created = self.db_insert_order(
                charge_point_id=charge_point_id,
                connector_id=connector_id,
                id_tag=id_tag,
                trigger_method=trigger_method,
                tenant_id=tenant_id,
                request_id = request_id
            )
            
            if not isinstance(order_created,Order):
                return order_created

            trans_det = f"Order created for {trigger_method}"
            
            transaction_created = self.db_insert_transaction(transaction_id=order_created.transaction_id,trans_det=trans_det)
            if not isinstance(transaction_created,Transaction):
                self.session.query(Order).filter(Order.transaction_id==order_created.transaction_id).delete()
                self.session.commit()
                return transaction_created
            
            logger.info(f"Transaction created: {transaction_created}")

            
            if isinstance(order_created,Order) and isinstance(transaction_created,Transaction):
                data["data"].update(
                    {
                        "transaction_id": order_created.transaction_id,
                        "connector_id": connector_id,
                        "id_tag": id_tag,
                        "trigger_method": trigger_method,
                        "start_time": start_time,
                        "is_reservation": False,
                        "is_charging": False,
                        "tenant_id": tenant_id,
                        "requires_payment": False,
                        "status_code": 201,
                    }
                )

                kafka_send(topic=MsEvDriverManagement.DriverVerificationRequest.value,data=data,request_id=request_id)

        except Exception as e:
            logger.error(f"(X) Error while creating order:{e}")
            self.session.rollback()
            return {"message": "create order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()
    
def kafka_send(topic: str, data: dict, request_id: str):
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
