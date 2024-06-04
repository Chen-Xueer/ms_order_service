import uuid
from flask_app.database_sessions import Database
from flask_app.services.common_function import DataValidation
from microservice_utils.settings import logger
from ms_tools.kafka_management.topics import MsEvDriverManagement, MsPaymentManagement
from sqlalchemy import and_, case, func, or_
from sqlalchemy.sql.functions import coalesce
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
    
    def list_order(self,tenant_id,transaction_id,keyword):
        try:
            tenant_exists = self.data_validation.validate_tenants(tenant_id)
            if tenant_exists is None:
                return {"message": "tenant_exists not found", "action":"order_retrieval","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},404
            
            if transaction_id is not None:
                filters = and_(Order.tenant_id == tenant_id, Order.transaction_id == transaction_id)
            else:
                filters = Order.tenant_id == tenant_id

            order_list = self.session.query(
                Order.transaction_id,
                Order.status,
                Order.charge_point_id,
                Order.connector_id,
                Order.ev_driver_id,
                Order.is_charging,
                Order.is_reservation,
                Order.requires_payment,
                Transaction.paid_by,
                Transaction.start_time,
                Transaction.end_time,
                Transaction.duration,
                Transaction.charged_energy,
                Transaction.amount,
                Transaction.transaction_detail
            ).outerjoin(Transaction, Order.transaction_id == Transaction.transaction_id).filter(filters).all()

            list_order = []
            append_count = 0
            for order in order_list:
                append_ind = False
                order_dict = {
                    "transaction_id": order[0],
                    "status": order[1],
                    "charge_point_id": order[2],
                    "connector_id": order[3],
                    "ev_driver_id": order[4],
                    "is_charging": order[5],
                    "is_reservation": order[6],
                    "requires_payment": order[7],
                    "paid_by": order[8],
                    "start_time": order[9].isoformat() if order[9] else None,
                    "end_time": order[10].isoformat() if order[10] else None,
                    "duration": order[11],
                    "charged_energy": order[12],
                    "amount": order[13],
                    "transaction_detail": order[14]
                }

                for value in order_dict.values():
                    if value is not None and keyword is not None and keyword.lower() in str(value).lower():
                        append_ind = True
                    
                if keyword is None:
                    append_ind = True
                
                if append_ind:
                    append_count += 1
                    order_dict["row_count"] = append_count
                    list_order.append(order_dict)

            return {"data": list_order}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"status": ReturnStatus.ERROR.value, "message": "Internal server error"}, 500
        finally:
            self.session.close()
    


    def list_transaction_summary(self,tenant_id):
        tenant_exists = self.data_validation.validate_tenants(tenant_id)
        if tenant_exists is None:
            return {"message": "tenant_exists not found", "action":"order_retrieval","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},404
        
        summary = self.session.query(
                                    Order.status,
                                    func.count(Order.status).label('count'),
                                    func.sum(coalesce(Transaction.amount,0)).label('total_amount')
                                ).outerjoin(
                                    Transaction,Order.transaction_id == Transaction.transaction_id
                                ).filter(
                                     Order.tenant_id == tenant_id
                                ).group_by(
                                    Order.status
                                ).all()
        logger.info(summary)
        return {"data":summary}
    


    def list_transaction_breakdown(self,tenant_id):
        tenant_exists = self.data_validation.validate_tenants(tenant_id)
        if tenant_exists is None:
            return {"message": "tenant_exists not found", "action":"order_retrieval","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},404
        
        status_case = case(
            *[(Order.status.in_([OrderStatus.AUTHORIZEDFAILED.value,OrderStatus.CANCELLED.value]),'failure')],
            else_='success'
        )

        summary = self.session.query(
                            status_case.label('transaction_status'),
                            func.count(Order.status).label('count')
                        ).filter(
                                     Order.tenant_id == tenant_id
                        ).group_by(
                            status_case
                        ).all()

        return {"data":summary}


        
