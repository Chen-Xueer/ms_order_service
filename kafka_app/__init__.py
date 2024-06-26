from kafka_app.handler import handler
from kafka_app.kafka_management.topic_enum import MsEvDriverManagement,MsPaymentManagement,MsOrderManagement,MsCSMSManagement


def app_init():
    from kafka_app.main import kafka_app

    # kafka_app.admin_client.delete_topics([MsOrderManagement.LIST_ORDER_REQUEST.value, MsOrderManagement.LIST_ORDER_RESPONSE.value, "ListOrderRequest1"])

    kafka_app.consume(
        [
            MsOrderManagement.CREATE_ORDER.value,
            MsOrderManagement.REJECT_ORDER.value,
            MsCSMSManagement.RESERVATION_RESPONSE.value,
            MsEvDriverManagement.DRIVER_VERIFICATION_RESPONSE.value,
            MsPaymentManagement.AUTHORIZE_PAYMENT_RESPONSE.value,
            MsOrderManagement.STOP_TRANSACTION.value,
            MsOrderManagement.LIST_ORDER_REQUEST.value,
        ],
        handler,
    )
