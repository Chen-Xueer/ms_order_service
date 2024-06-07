import pytest
from unittest.mock import patch, Mock
from kafka_app import app_init
from kafka_app.handler import handler
from kafka_app.kafka_management.topic_enum import MsEvDriverManagement,MsPaymentManagement,MsOrderManagement,MsCSMSManagement

#@patch('kafka_app.main.kafka_app')
#def test_app_init(mock_kafka_app):
#    # Arrange
#    mock_kafka_app.consume = Mock()
#
#    # Act
#    app_init()
#
#    # Assert
#    mock_kafka_app.consume.assert_called_once_with(
#        [
#            MsOrderManagement.CREATE_ORDER.value,
#            MsOrderManagement.REJECT_ORDER.value,
#            MsCSMSManagement.RESERVATION_RESPONSE.value,
#            MsEvDriverManagement.DRIVER_VERIFICATION_RESPONSE.value,
#            MsPaymentManagement.AUTHORIZE_PAYMENT_RESPONSE.value,
#            MsOrderManagement.STOP_TRANSACTION.value,
#        ],
#        handler,
#    )