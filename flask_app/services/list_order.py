import os
from flask_app.database_sessions import Database
from flask_app.services.common_function import DataValidation
from flask_app.services.models import ListOrderModel
from microservice_utils.settings import logger
from kafka_app.kafka_management.topic_enum import MsEvDriverManagement, MsPaymentManagement
from sqlalchemy import Float, String, and_, case, func, literal_column, or_, cast
from sqlalchemy.sql.functions import coalesce
from sqlalchemy_.ms_order_service.enum_types import ReturnActionStatus, ReturnStatus, OrderStatus
from sqlalchemy_.ms_order_service.order import Order
from sqlalchemy_.ms_order_service.tenant import Tenant
from sqlalchemy_.ms_order_service.transaction import Transaction
import requests
from dotenv import load_dotenv

load_dotenv()
GET_API_EV_DRIVER = os.getenv("GET_API_EV_DRIVER")

class ListOrder:
    def __init__(self):
        database = Database()
        self.session = database.init_session()
        self.data_validation = DataValidation()
    
    def list_order(self,data:ListOrderModel):
        try:
            # tenant_exists = self.data_validation.validate_tenants(tenant_id=data.tenant_id,action='order_retrieval')
            # if not isinstance(tenant_exists,Tenant):
            #     return tenant_exists

            query = self.session.query(
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
                coalesce(Transaction.amount,0).label("amount"),
                Transaction.transaction_detail
            ).outerjoin(
                Transaction, Order.transaction_id == Transaction.transaction_id
            ).filter(
                Order.tenant_id == data.tenant_id
            )

            # Conditionally add filter if data.ev_driver_id is not None
            if data.ev_driver_id is not None:
                query = query.filter(Order.ev_driver_id == data.ev_driver_id)

            if data.transaction_id is not None:
                query = query.filter(Order.transaction_id == data.transaction_id)

            # Execute the query
            order_list = query.all()
            
            list_order = []
            append_count = 0
            for order in order_list:
                append_ind = False
                order = ListOrderModel(**order._asdict())

                if data.keyword is not None:
                    if order.search_keyword(data.keyword):
                        append_ind = True
                else:
                    append_ind = True
                
                if append_ind:
                    append_count += 1
                    order = order.__dict__
                    order["row_count"] = append_count
                    list_order.append(order)

            # formatted_results = []
            # for order in list_order:
            #     if list_order['start_time'] or list_order['end_time']:
            #         list_order['start_time'] = list_order['start_time'].isoformat()
                # formatted_results.append(formatted_result)

            return {"data": list_order}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"status": ReturnStatus.ERROR.value, "message": "Internal server error"}, 500
        finally:
            self.session.close()
    


    def list_transaction_summary(self,tenant_id):
        try:
            tenant_exists = self.data_validation.validate_tenants(tenant_id=tenant_id,action='transaction_summary_retrieval')
            if not isinstance(tenant_exists,Tenant):
                return tenant_exists     

            summary = self.session.query(
                                        Order.ev_driver_id,
                                        literal_column("'site_name'").label("site_name"),
                                        literal_column("'device_name'").label("device_name"),
                                        Order.transaction_id,
                                        Transaction.start_time,
                                        Transaction.end_time,
                                        Transaction.duration,
                                        Transaction.charged_energy,
                                        Transaction.amount
                                    ).outerjoin(
                                        Transaction,Order.transaction_id == Transaction.transaction_id
                                    ).filter(
                                         Order.tenant_id == tenant_id
                                    ).all()
            ev_driver_list = []
            data=[]
            for rec in summary:
                filtered_list = [driver for driver in ev_driver_list if driver['ev_driver_id'] == rec.ev_driver_id]
                if len(filtered_list) == 0:
                    driver_api = requests.get(f"{GET_API_EV_DRIVER}{rec.ev_driver_id}")
                    if driver_api.status_code == 200:
                        driver_api = driver_api.json().get('data',None)
                        driver_api['ev_driver_id'] = rec.ev_driver_id
                        ev_driver_list.append(driver_api)
                        filtered_list = [driver for driver in ev_driver_list if driver['ev_driver_id'] == rec.ev_driver_id][0]
                        logger.info(f"filtered_list:{filtered_list}")
                else:
                    filtered_list = filtered_list[0]
                
                data.append(
                    {
                        "driver":filtered_list.get('driver',None),
                        "email":filtered_list.get('email',None),
                        "site_name":rec.site_name,
                        "device_name":rec.device_name,
                        "start":rec.start_time,
                        "stop":rec.end_time,
                        "duration":rec.duration,
                        "charged_energy":rec.charged_energy,
                        "total_cost":rec.amount,
                    }
                )

            logger.info(data)
            return {"data": data, "action": "transaction_summary_retrieval", "action_status": ReturnActionStatus.COMPLETED.value,"status":ReturnStatus.SUCCESS.value},200
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"message": "list transaction summary failed", "action":"transaction_summary_retrieval","action_status":ReturnActionStatus.FAILED.value,"status": ReturnStatus.ERROR.value},500


    def list_transaction_breakdown(self,tenant_id):
        tenant_exists = self.data_validation.validate_tenants(tenant_id=tenant_id,action='transaction_breakdown_retrieval')
        if not isinstance(tenant_exists,Tenant):
            return tenant_exists
        
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
        
