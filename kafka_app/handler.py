import json
from flask_app.services.common_function import DataValidation, kafka_out
from microservice_utils.settings import logger
from kafka_app.kafka_management.topic_enum import MsOrderManagement, MsEvDriverManagement,MsPaymentManagement,MsCSMSManagement
from flask_app.services.models import KafkaPayload, ListOrderModel, ValidateKafkaMessageModel
from kafka_app.kafka_management.kafka_topic import KafkaMessage
from flask_app.database_sessions import Database
from flask_app.services.update_order import UpdateOrder 
from flask_app.services.list_order import ListOrder

def handler(message: KafkaMessage):
    try:
        logger.info(
            f"Handling message: {message.key} {message.topic} {message.headers} {json.dumps(message.payload)}"
        )

        data = message.payload
        logger.info(f"data: {data.get('data')}")

        validate_model = validate_request(message)
        logger.info(f"{validate_model}")

        if validate_model.count_errors() > 0:
            data["data"].update({'status_code':400,'error_description': validate_model.to_dict()})

            update_order = UpdateOrder()  
            update_order.update_order(data = KafkaPayload(**data),cancel_ind = True)
        else:
            if message.topic == MsOrderManagement.CREATE_ORDER.value:
                logger.info(f"Creating Order: {data}")

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
                MsOrderManagement.STOP_TRANSACTION.value,
                MsOrderManagement.CANCEL_RESERVATION.value,
                MsOrderManagement.START_TRANSACTION.value,
                MsOrderManagement.TRANSACTION_STARTED.value,
                MsOrderManagement.START_TRANSACTION_REQUEST.value,
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
                kafka_out(topic=MsOrderManagement.LIST_ORDER_RESPONSE.value, data=output, request_id=message.payload.get("meta").get("request_id"))
                       
    except Exception as e:
        logger.error(e)



def validate_request(message: KafkaMessage):
    validate_model = ValidateKafkaMessageModel()

    logger.info(f"topic: {message.topic}")
    if message.topic not in [
        MsOrderManagement.CREATE_ORDER.value,
        MsEvDriverManagement.DRIVER_VERIFICATION_RESPONSE.value,
        MsCSMSManagement.RESERVATION_RESPONSE.value,
        MsPaymentManagement.AUTHORIZE_PAYMENT_RESPONSE.value,
        MsOrderManagement.REJECT_ORDER.value,
        MsOrderManagement.STOP_TRANSACTION.value,
        MsOrderManagement.LIST_ORDER_REQUEST.value,
        MsOrderManagement.CANCEL_RESERVATION.value,
        MsOrderManagement.START_TRANSACTION.value,
        MsOrderManagement.TRANSACTION_STARTED.value,
        MsOrderManagement.START_TRANSACTION_REQUEST.value,
    ]:
        logger.info("Action Not Implemented")
        validate_model.action = "Action Not Implemented"
    
    #if message.payload.get('data').get('status') == 'Rejected':
    #    validate_model.status = "Rejected"

    #action = message.payload.get("meta").get("action")
    #validate.update(data_validate.validate_null(value=action,field_name="action"))

    #transaction_id = message.payload.get("data").get("transaction_id")
    #validate.update(data_validate.validate_transaction_id(transaction_id=transaction_id,action=data.meta.action))
    #
    #request_id = message.payload.get("meta").get("request_id")
    #validate.update(data_validate.validate_null(value=request_id,field_name="request_id"))
    #
    #requires_payment = message.payload.get("data").get("requires_payment")
    #validate.update(data_validate.validate_null(value=requires_payment,field_name="requires_payment"))

    
    #id_tag = message.payload.get("data").get("id_tag")
    #logger.info(f"id_tag: {id_tag}")
    #mobile_id = message.payload.get("data").get("mobile_id")
    #logger.info(f"mobile_id: {mobile_id}")

    #if id_tag is None and mobile_id is None:
    #    validate.update({"error_description": {"id_tag": "rfid or mobile_id is required"}, "status": 400})

    if validate_model.count_errors() > 0:
        logger.error("Validation Failed")
        return validate_model
    
    logger.info(f"validate_model: {validate_model.to_dict()}")
    
    logger.info("Validation Passed")
    return validate_model
      



