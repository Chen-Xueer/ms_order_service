from kafka_app.handler import handler
from kafka_app.kafka_management.topic_enum import MsEvDriverManagement,MsPaymentManagement,MsOrderManagement,MsCSMSManagement


def app_init():
    from kafka_app.main import kafka_app

    kafka_app.admin_client.delete_topics([
        'CreateOrder','CreateOrderResponse',
        'RejectOrder','OrderRejected',
        'DriverVerificationRequest','DriverVerificationResponse',
        'AuthorizeResponse',
        'ReservationRequest','ReservationResponse',
        'RemoteControlRequest','RemoteControlResponse',
        'GetDriverInfoRequest','GetDriverInfoResponse',
        'StopTransaction','StopTransactionResponse',
        'CancelReservation',
        'MeterValue','MeterValuesResponse',
        'StartTransaction','StartTransactionResponse',
        'TransactionStatus',
        'StartTransactionRequest','StartTransactionRequestResponse',
    ])

    kafka_app.consume(
        [
            MsOrderManagement.CREATE_ORDER.value,
            MsOrderManagement.REJECT_ORDER.value,
            MsCSMSManagement.RESERVATION_RESPONSE.value,
            MsEvDriverManagement.DRIVER_VERIFICATION_RESPONSE.value,
            MsPaymentManagement.AUTHORIZE_PAYMENT_RESPONSE.value,
            MsOrderManagement.STOP_TRANSACTION.value,
            MsOrderManagement.LIST_ORDER_REQUEST.value,
            MsOrderManagement.CANCEL_RESERVATION.value,
            MsOrderManagement.START_TRANSACTION.value,
            MsOrderManagement.TRANSACTION_STARTED.value,
            MsOrderManagement.START_TRANSACTION_REQUEST.value,
        ],
        handler,
    )
