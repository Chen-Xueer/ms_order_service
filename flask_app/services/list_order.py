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

class ListOrder:
    def __init__(self):
        database = Database()
        self.session = database.init_session()
        self.data_validation = DataValidation()
    
    def list_order(self,transaction_id,tenant_id):
        try:
            order_exists = self.session.query(Order).filter(Order.transaction_id == transaction_id).first()
            if order_exists is None:
                return {"message": "Order not found", "action":"order_retrieval","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},404

            transaction_exists = self.session.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
            if transaction_exists is None:
                return {"message": "Transaction not found", "action":"order_retrieval","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},404
            
            data = {}
            data.update(
                {
                    "meta": {
                        "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "version":"1.0.0",
                        "type": "order_retrieval",
                        "action": "ListTransactionDetails"
                    },
                    "data": {
                        "transaction_id": transaction_exists.transaction_id,
                        "paid_by": transaction_exists.paid_by,
                        "start_time": transaction_exists.start_time,
                        "end_time": transaction_exists.end_time,
                        "duration": transaction_exists.duration,
                        "charged_energy": transaction_exists.charged_energy,
                        "amount": transaction_exists.amount,
                        "status": order_exists.status,
                        "charge_point_id": order_exists.charge_point_id,
                        "connector_id": order_exists.connector_id,
                        "transaction_detail": transaction_exists.transaction_detail
                    }
                }
            )
            
            logger.info(f"Order details: {data}")

            return data, 200
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"status": ReturnStatus.ERROR.value, "message": "Internal server error"}, 500
        finally:
            self.session.close()