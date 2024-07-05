import datetime
import json
from flask_app.services.common_function import DataValidation, kafka_out
from microservice_utils.settings import logger
from kafka_app.kafka_management.topic_enum import MsOrderManagement, MsEvDriverManagement,MsPaymentManagement,MsCSMSManagement
from flask_app.services.models import KafkaPayload, ListOrderModel
from kafka_app.kafka_management.kafka_topic import KafkaMessage,Topic
from flask_app.database_sessions import Database
from flask_app.services.update_order import UpdateOrder 
from flask_app.services.list_order import ListOrder
from sqlalchemy_.ms_order_service.enum_types import TriggerMethod

def handler(message: KafkaMessage):
    try:
        database= Database()
        session=database.init_session()
        logger.info("Database Initialized")

        logger.info(
            f"Handling message: {message.key} {message.topic} {message.headers} {json.dumps(message.payload)}"
        )

        validate_result,validate = validate_request(message)
        logger.info(f"{validate_result}")
        logger.info(f"{validate_result != None}")
        data = message.payload
        logger.info(f"data: {data.get('data')}")

        if validate_result == False:
            data.get('data').update(validate)
            update_order = UpdateOrder()  
            update_order.update_order(data = KafkaPayload(**data),cancel_ind = True)

        if message.topic == MsOrderManagement.CREATE_ORDER.value:
            from flask_app.services.create_order import CreateOrder
            create_order = CreateOrder()            
            data = KafkaPayload(**data)
            create_order.create_order(data = data)

        if message.topic == MsOrderManagement.REJECT_ORDER.value:
            update_order = UpdateOrder()   
            update_order.update_order(data = KafkaPayload(**data),cancel_ind = True)

        if message.topic in (
            MsEvDriverManagement.DRIVER_VERIFICATION_RESPONSE.value,
            MsCSMSManagement.RESERVATION_RESPONSE.value,
            MsPaymentManagement.AUTHORIZE_PAYMENT_RESPONSE.value,
            MsPaymentManagement.CANCEL_PAYMENT_RESPONSE.value,
            MsOrderManagement.STOP_TRANSACTION.value
        ):
            logger.info(f"Updating Order: {data}")
            update_order = UpdateOrder()   
            update_order.update_order(data = KafkaPayload(**data),cancel_ind = None)

        if message.topic == MsOrderManagement.LIST_ORDER_REQUEST.value:
            list_order = ListOrder()
            payload = data.get("data")
            response = list_order.list_order(data=ListOrderModel(**payload))
            data["meta"]["producer"] = "OrderService"
            data["meta"]["type"] = MsOrderManagement.LIST_ORDER_RESPONSE.value
            output = {
                "meta": data["meta"],
                "data": response
            }
            kafka_out(topic=MsOrderManagement.LIST_ORDER_RESPONSE.value, data=output, request_id=message.headers["request_id"])
                       
    except Exception as e:
        session.rollback()
        logger.error(e)
    finally:
        session.close()



def validate_request(message: KafkaMessage):
    data_validate = DataValidation()
    validate = {}

    logger.info(f"topic: {message.topic}")
    if message.topic not in [
        MsOrderManagement.CREATE_ORDER.value,
        MsEvDriverManagement.DRIVER_VERIFICATION_RESPONSE.value,
        MsCSMSManagement.RESERVATION_RESPONSE.value,
        MsPaymentManagement.AUTHORIZE_PAYMENT_RESPONSE.value,
        MsOrderManagement.REJECT_ORDER.value,
        MsOrderManagement.STOP_TRANSACTION.value,
        MsOrderManagement.LIST_ORDER_REQUEST.value
    ]:
        logger.info("Action Not Implemented")
        validate.update({"error_description": {"action": "Action Not Implemented"}, "status_code": 404})

    #trigger_method = message.payload.get("data").get("trigger_method")
    #validate.update(data_validate.validate_null(value=trigger_method,field_name="trigger_method"))

    #transaction_id = message.payload.get("data").get("transaction_id")
    #validate.update(data_validate.validate_transaction_id(transaction_id=transaction_id,trigger_method=trigger_method))
    #
    #request_id = message.payload.get("meta").get("request_id")
    #validate.update(data_validate.validate_null(value=request_id,field_name="request_id"))
    #
    #payment_required = message.payload.get("data").get("payment_required")
    #validate.update(data_validate.validate_null(value=payment_required,field_name="payment_required"))

    
    #id_tag = message.payload.get("data").get("id_tag")
    #logger.info(f"id_tag: {id_tag}")
    #mobile_id = message.payload.get("data").get("mobile_id")
    #logger.info(f"mobile_id: {mobile_id}")

    #if id_tag is None and mobile_id is None:
    #    validate.update({"error_description": {"id_tag": "rfid or mobile_id is required"}, "status": 400})

    logger.info(f"validate: {validate}")
    if len(validate) > 0:
        logger.error("Validation Failed")
        return False,validate
    
    logger.info("Validation Passed")
    return True,None
      



