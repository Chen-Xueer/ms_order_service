import pytest
from unittest.mock import ANY, Mock,MagicMock, patch
import sys
from pathlib import Path

from flask_app.services.models import KafkaEVSE, KafkaMeta, KafkaPayload, ReservationPayload, StartTransactionPayload
from sqlalchemy_.ms_order_service.transaction import Transaction
sys.path.append(str(Path(__file__).resolve().parent.parent))
from flask_app.services.update_order import UpdateOrder, kafka_out
from sqlalchemy_.ms_order_service.order import Order
from flask_app.services.common_function import DataValidation
from sqlalchemy_.ms_order_service.enum_types import OrderStatus, ProducerTypes,TriggerMethod
from kafka_app.kafka_management.topic_enum import MsCSMSManagement,MsEVSEManagement,MsPaymentManagement,MsOrderManagement
from datetime import datetime

def test_update_order_none():
    # Create a mock KafkaPayload object
    data = Mock(spec=KafkaPayload)
    data.expiry_date = None
    data.transaction_id = '123'
    data.trigger_method = TriggerMethod.START_TRANSACTION.value
    data.meta = Mock(spec=KafkaMeta)
    data.meta.request_id = '456'

    # Mock the methods of DataValidation and CreateOrder classes
    with patch('flask_app.services.common_function.DataValidation.validate_order', return_value=None) as mock_validate_order, \
         patch('flask_app.services.common_function.DataValidation.validate_order_request', return_value=None) as mock_validate_order_request, \
         patch('flask_app.services.create_order.CreateOrder.create_order_rfid', return_value=None) as mock_create_order_rfid:

        update_order = UpdateOrder()
        result = update_order.update_order(data, cancel_ind=False)

        # Check if the validate_order method was called with the correct argument
        mock_validate_order.assert_called_once_with(transaction_id='123')

        # Check if the validate_order_request method was called with the correct argument
        mock_validate_order_request.assert_called_once_with(request_id='456')

        # Check if the create_order_rfid method was called with the correct argument
        mock_create_order_rfid.assert_called_once_with(data=data)

        # Check if the result is an instance of Order
        assert result == None

def test_update_order_start_transaction():
    # Create a mock KafkaPayload object
    data = Mock(spec=KafkaPayload)
    data.expiry_date = None
    data.transaction_id = '123'
    data.id_tag = 'RFID_001'
    data.status = OrderStatus.AUTHORIZED.value
    data.trigger_method = TriggerMethod.START_TRANSACTION.value
    data.meta = Mock(spec=KafkaMeta)
    data.meta.request_id = '456'
    data.meta.producer = ProducerTypes.OCPP_AS_SERVICE.value
    data.evse = Mock(spec=KafkaEVSE)
    data.evse.subprotocol = 'OCPP1.6'
    data.evse.charge_point_id = 'CP_001'

    # Create a mock Order object
    mock_order = Mock(spec=Order)
    mock_order.status = OrderStatus.AUTHORIZED.value
    mock_order.transaction_id = '123'

    mock_transaction = Mock(spec=Transaction)
    mock_transaction.transaction_detail = "Initial detail"

    mock_session = Mock()
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.update = MagicMock()

    mock_update = {
        "charge_point_id": data.evse.charge_point_id,
        "connector_id": data.connector_id,
        "ev_driver_id": data.id_tag,
        "is_charging": None,
        "is_reservation": None,
        "requires_payment": data.requires_payment,
        "tenant_id": data.tenant_id,
        "status": None,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Mock the methods of DataValidation and CreateOrder classes
    with patch('flask_app.services.common_function.DataValidation.validate_order', return_value=None) as mock_validate_order, \
         patch('flask_app.services.common_function.DataValidation.validate_order_request', return_value=None) as mock_validate_order_request, \
         patch('flask_app.services.create_order.CreateOrder.create_order_rfid', return_value=mock_order) as mock_create_order_rfid, \
         patch('flask_app.services.common_function.DataValidation.validate_transaction', return_value=mock_transaction) as mock_validate_transaction, \
         patch('flask_app.services.update_order.Database.init_session', return_value = mock_session) as mock_init_session, \
         patch.object(mock_session, 'filter', return_value=mock_filter) as filter_mock, \
         patch.object(mock_session, 'update', return_value=mock_update) as update_mock, \
         patch('flask_app.services.update_order.kafka_out') as mock_kafka_out:
    
        update_order = UpdateOrder()
        update_order.update_order(data, cancel_ind=False)

        # Check if the validate_order method was called with the correct argument
        mock_validate_order.assert_called_once_with(transaction_id='123')

        # Check if the validate_order_request method was called with the correct argument
        mock_validate_order_request.assert_called_once_with(request_id='456')

        # Check if the create_order_rfid method was called with the correct argument
        mock_create_order_rfid.assert_called_once_with(data=data)

        # Check if the validate_transaction method was called with the correct argument
        mock_validate_transaction.assert_called_once_with(transaction_id='123')

        mock_session.commit.assert_called_once()

        mock_filter.update.assert_called_once_with(
            mock_update
        )

        mock_session.commit.assert_called_once()

        # Assert that the data object and kafka_topic have the expected values
        assert data.meta.meta_type == "RemoteControlResponse"
        mock_kafka_out.called

def test_update_order_make_reservation():
    # Create a mock KafkaPayload object
    data = Mock(spec=KafkaPayload)
    data.expiry_date = None
    data.transaction_id = '123'
    data.id_tag = 'RFID_001'
    data.status = OrderStatus.AUTHORIZED.value
    data.trigger_method = TriggerMethod.MAKE_RESERVATION.value
    data.meta = Mock(spec=KafkaMeta)
    data.meta.request_id = '456'
    data.meta.producer = ProducerTypes.OCPP_AS_SERVICE.value
    data.meta.meta_type = "RemoteControlResponse"
    data.evse = Mock(spec=KafkaEVSE)
    data.evse.subprotocol = 'OCPP1.6'
    data.evse.charge_point_id = 'CP_001'

    # Create a mock Order object
    mock_order = Mock(spec=Order)
    mock_order.status = OrderStatus.AUTHORIZED.value
    mock_order.transaction_id = '123'

    mock_transaction = Mock(spec=Transaction)
    mock_transaction.transaction_detail = "Initial detail"

    mock_session = Mock()
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.update = MagicMock()

    mock_update = {
        "charge_point_id": data.evse.charge_point_id,
        "connector_id": data.connector_id,
        "ev_driver_id": data.id_tag,
        "is_charging": None,
        "is_reservation": None,
        "requires_payment": data.requires_payment,
        "tenant_id": data.tenant_id,
        "status": None,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Mock the methods of DataValidation and CreateOrder classes
    with patch('flask_app.services.common_function.DataValidation.validate_order', return_value=mock_order) as mock_validate_order, \
         patch('flask_app.services.common_function.DataValidation.validate_order_request', return_value=None) as mock_validate_order_request, \
         patch('flask_app.services.create_order.CreateOrder.create_order_rfid', return_value=mock_order) as mock_create_order_rfid, \
         patch('flask_app.services.common_function.DataValidation.validate_transaction', return_value=mock_transaction) as mock_validate_transaction, \
         patch('flask_app.services.update_order.Database.init_session', return_value = mock_session) as mock_init_session, \
         patch.object(mock_session, 'filter', return_value=mock_filter) as filter_mock, \
         patch.object(mock_session, 'update', return_value=mock_update) as update_mock, \
         patch('flask_app.services.update_order.kafka_out') as mock_kafka_out:
    
        update_order = UpdateOrder()
        update_order.update_order(data, cancel_ind=False)

        # Check if the validate_order method was called with the correct argument
        mock_validate_order.assert_called_once_with(transaction_id='123')

        # Check if the validate_transaction method was called with the correct argument
        mock_validate_transaction.assert_called_once_with(transaction_id='123')

        mock_session.commit.assert_called_once()

        mock_filter.update.assert_called_once_with(
            mock_update
        )

        mock_session.commit.assert_called_once()

        # Assert that the data object and kafka_topic have the expected values
        assert data.meta.meta_type == "RemoteControlResponse"
        mock_kafka_out.called
        
@patch('kafka_app.main.kafka_app')
def test_kafka_send(mock_kafka_app):
    # Arrange
    topic = "test_topic"
    data = {"key": "value"}
    request_id = "test_request_id"
    mock_kafka_app.send.return_value = None  # Assuming the send method returns None on success
    # Act
    kafka_out(topic, data, request_id)
    # Assert
    mock_kafka_app.send.assert_called_once()