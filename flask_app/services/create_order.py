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
    def init(self):
        self.database = Database()
        self.session = self.database.init_session()
        self.data_validation = DataValidation()
    
    def db_insert_order(self,**kwargs):
        try:
            data = kwargs.get("data")
            tenant = data.get("data").get("tenant")
            charge_point_id = data.get("data").get("charge_point_id")
            connector_id = data.get("data").get("connector_id")
            mobile_id = data.get("data").get("driver_id")
            rfid = data.get("data").get("rfid")
            trigger_method = data.get("meta").get("trigger_method")
            
            if 'start_charging' in trigger_method:
                charge_ind=True
            else:
                charge_ind=False
            
            if 'make_reservation' in trigger_method:
                reservation_ind=True
            else:
                reservation_ind=False

            order_created = Order(
                            tenant=tenant,
                            status=OrderStatus.CREATED.value,
                            charge_point_id=charge_point_id,
                            connector_id=connector_id,
                            driver_id=mobile_id,
                            rfid=rfid,
                            tariff_id=None,
                            charging_ind=charge_ind,
                            reservation_ind=reservation_ind,
                            payment_required_ind=False,
                            create_dt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            modify_dt=None
                        )
            self.session.add(order_created)
            self.session.commit()
            return order_created
        except Exception as e:
            logger.error(f"(X) Error while creating order: {e}")
            self.session.rollback()
            return {"message": "insert order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500

    def db_insert_transaction(self,transactional_id):
        try:
            transaction_created = Transaction(
                            transactional_id=transactional_id,
                            amount=None,
                            energy_charged=None,
                            duration=None,
                            paid_by=None,
                            trans_det=None
                        )
            self.session.add(transaction_created)
            self.session.commit()
            return transaction_created
        except Exception as e:
            logger.error(f"(X) Error while creating transaction: {e}")
            self.session.rollback()
            return {"message": "insert transaction failed", "action":"transaction_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500


    def create_order_mobile_id(self,mobile_id,data,tenant):
        try:
            data = data["meta"].update(
                {
                    "service_name":"ms_order_service",
                    "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version":"1.0.0",
                    "type": "order_creation"
                }
            )
        
            charge_point_id = data.get("data").get("charge_point_id")
            connector_id = data.get("data").get("connector_id")
            trigger_method = data.get("data").get("trigger_method")
            request_id = str(uuid.uuid4())
            requires_payment = data.get("data").get("requires_payment")

            order_created = self.db_insert_order(data=data)
            if not isinstance(order_created,Order):
                return order_created
            
            transaction_created = self.db_insert_transaction(order_created.transactional_id)
            if not isinstance(transaction_created,Transaction):
                self.session.query(Order).filter(Order.transactional_id==order_created.transactional_id).delete()
                self.session.commit()
                return transaction_created
            
            if isinstance(order_created,Order) and isinstance(transaction_created,Transaction):
                data = {
                    "meta": {
                        "request_id": request_id,
                        "timestamp": order_created.create_dt,
                        "producer": "ms_order_service",
                        "version": "1.0",
                        "type": "order_creation"
                    },
                    "data": {
                        "transaction_id": order_created.transactional_id,
                        "charge_point_id": charge_point_id,
                        "connector_id": connector_id,
                        "mobile_id": mobile_id,
                        "trigger_method": trigger_method,
                        "start_time": order_created.start_time,
                        "is_reservation": False,
                        "is_charging": False,
                        "tenant": tenant,
                        "requires_payment": False,
                        "status": "success",
                        "status_code": 201,
                    }
                }

                kafka_send(topic=MsEvDriverManagement.DriverVerificationRequest.value,data=data,request_id=request_id)

                response = kafka_out_wait_response(topic=MsEvDriverManagement.DriverVerificationRequest.value,data=data,return_topic=MsEvDriverManagement.DriverVerificationResponse.value)

                if response.get("data").get("status") == "200":
                    self.session.query(Order).filter(Order.transactional_id==order_created.transactional_id).update({"status":OrderStatus.AUTHORIZED.value})
                    self.session.commit()

                if response.get("data").get("status") == "400":
                    self.session.query(Order).filter(Order.transactional_id==order_created.transactional_id).update({"status":OrderStatus.AUTHORIZEDFAILED.value})
                    self.session.commit()
                    if requires_payment == True:
                        kafka_send(topic=MsPaymentManagement.CancelPaymentRequest.value,data=data,request_id=request_id)
        
        except Exception as e:
            logger.error(f"(X) Error while creating order: {e}")
            self.session.rollback()
            return {"message": "create order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
        finally:
            self.session.close()
    
    def create_order_rfid(self,data):
        data = data["meta"].update(
            {
                "service_name":"ms_order_service",
                "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version":"1.0.0",
                "type": "order_creation"
            }
        )

        try:
            rfid = data.get("data").get("rfid")
            tenant = data.get("data").get("tenant")
            charge_point_id = data.get("data").get("charge_point_id")
            connector_id = data.get("data").get("connector_id")
            trigger_method = data.get("data").get("trigger_method")
            request_id = str(uuid.uuid4())
            requires_payment = data.get("data").get("requires_payment")

            order_created = self.db_insert_order(data=data)
            if not isinstance(order_created,Order):
                return order_created
            
            transaction_created = self.db_insert_transaction(order_created.transactional_id)
            if not isinstance(transaction_created,Transaction):
                self.session.query(Order).filter(Order.transactional_id==order_created.transactional_id).delete()
                self.session.commit()
                return transaction_created
            
            if isinstance(order_created,Order) and isinstance(transaction_created,Transaction):
                data = {
                    "meta": {
                        "request_id": request_id,
                        "timestamp": order_created.create_dt,
                        "producer": "ms_order_service",
                        "version": "1.0",
                        "type": "order_creation"
                    },
                    "data": {
                        "transaction_id": order_created.transactional_id,
                        "charge_point_id": charge_point_id,
                        "connector_id": connector_id,
                        "rfid": rfid,
                        "trigger_method": trigger_method,
                        "start_time": order_created.start_time,
                        "is_reservation": False,
                        "is_charging": False,
                        "tenant": tenant,
                        "requires_payment": False,
                        "status": "success",
                        "status_code": 201,
                    }
                }

                response = kafka_out_wait_response(topic=MsEvDriverManagement.DriverVerificationRequest.value,data=data,return_topic=MsEvDriverManagement.DriverVerificationResponse.value)

                if response.get("data").get("status") == "200":
                    self.session.query(Order).filter(Order.transactional_id==order_created.transactional_id).update({"status":OrderStatus.AUTHORIZED.value})
                    self.session.commit()

                if response.get("data").get("status") == "400":
                    self.session.query(Order).filter(Order.transactional_id==order_created.transactional_id).update({"status":OrderStatus.AUTHORIZEDFAILED.value})
                    self.session.commit()
                    if requires_payment == True:
                        kafka_send(topic=MsPaymentManagement.CancelPaymentRequest.value,data=data,request_id=request_id)

        except Exception as e:
            logger.error(f"(X) Error while creating order: {e}")
            self.session.rollback()
            return {"message": "create order failed", "action":"order_creation","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500
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



def kafka_out_wait_response(topic, data,return_topic):
    from kafka_app.main import kafka_app
    from ms_tools.kafka_management.kafka_topic import Topic
    response = kafka_app.send(
        topic=Topic(
            name=topic,
            data=data,
            return_topic=return_topic,
        ),
    )
    return response.payload