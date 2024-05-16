from kafka_app.handler import handler
from ms_tools.kafka_management.topics import MsEvDriverManagement,MsPaymentManagement,MsOrderManagement


def app_init():
    from kafka_app.main import kafka_app

    kafka_app.consume(
        [
            MsOrderManagement.CreateOrder.value,
            MsOrderManagement.RejectOrder.value,
            MsEvDriverManagement.DriverVerificationResponse.value,
            MsPaymentManagement.AuthorizePaymentResponse.value,
        ],
        handler,
    )
