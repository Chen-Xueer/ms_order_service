import json
from microservice_utils.settings import logger
from ms_tools.kafka_management.topics import MsOrderManagement, MsEvDriverManagement,MsPaymentManagement
from ms_tools.kafka_management.kafka_topic import Topic,KafkaMessage
from flask_app.database_sessions import Database
from flask_app.services.create_order import CreateOrder
from flask_app.services.update_order import UpdateOrder

database= Database()
session=database.init_session()
logger.info("Database Initialized")


def handler(message: KafkaMessage):
    try:
        logger.info(
            f"Handling message: {message.key} {message.topic} {message.headers} {json.dumps(message.payload)}"
        )

        validate_result,validate = validate_request(message)

        data = message.payload

        if not validate_result:
            data = data["data"].update(validate)
            update_order = UpdateOrder()   
            update_order.update_order(data = data)
        
        if message.topic == MsOrderManagement.CreateOrder.value:
            create_order = CreateOrder()
            create_order.create_order_rfid(data = data)
            
        if message.topic in (
            MsOrderManagement.RejectOrder.value
        ):
            update_order = UpdateOrder()   
            update_order.update_order(data = data)   
        
        if message.topic in [MsEvDriverManagement.DriverVerificationResponse.value]:
            from kafka_app.main import kafka_app
            kafka_app.router.put_message(message)
   
    except Exception as e:
        session.rollback()
        logger.error(e)
    finally:
        session.close()



def validate_request(message: KafkaMessage):
    validate = {"error_description":{}}

    if message.topic not in [
        MsOrderManagement.CreateOrder.value,
        MsEvDriverManagement.DriverVerification.value,
        MsPaymentManagement.AuthorizePayment.value,
        MsOrderManagement.RejectOrder.value,
    ]:
        logger.info("Action Not Implemented")
        validate["error_description"]["action"] = "Action Not Implemented"
        validate["status"] = 404
    
    request_id = message.payload.get("meta").get("request_id")
    logger.info(f"request_id: {request_id}")
    if request_id is None:
        validate["error_description"]["request_id"] = "request_id is required"
        validate["status"] = 400
    
    trigger_method = message.payload.get("data").get("trigger_method")
    logger.info(f"trigger_method: {trigger_method}")
    if trigger_method is None:
        validate["error_description"]["trigger_method"] = "trigger_method is required"
        validate["status"] = 400
    
    payment_required = message.payload.get("data").get("payment_required")
    logger.info(f"payment_required: {payment_required}")
    if payment_required is None:
        message.payload["data"]["payment_required"] = False

    id_tag = message.payload.get("data").get("id_tag")
    logger.info(f"id_tag: {id_tag}")
    mobile_id = message.payload.get("data").get("cognito_user_id")
    logger.info(f"mobile_id: {mobile_id}")

    if id_tag is None and mobile_id is None:
        validate["error_description"]["id_tag"] = "id_tag or mobile_id is required"
        validate["error_description"]["mobile_id"] = "id_tag or mobile_id is required"
        validate["status"] = 400

    logger.info(f"validate: {validate}")
    if len(validate["error_description"]) > 0:
        logger.error("Validation Failed")
        return False,validate
    
    logger.info("Validation Passed")
    return True,None
      




def kafka_out(topic: str, data: dict, request_id: str):
    from kafka_app.main import kafka_app
    kafka_app.send(
        topic=Topic(
            name=topic,
            data=data,
        ),
        request_id=request_id
    )


def kafka_out_wait_response(topic, data,return_topic):
    from kafka_app.main import kafka_app
    response = kafka_app.send(
        topic=Topic(
            name=topic,
            data=data,
            return_topic=return_topic,
        ),
    )
    return response.payload