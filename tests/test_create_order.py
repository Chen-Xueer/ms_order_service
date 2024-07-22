import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

from flask_app.services.models import KafkaPayload
from sqlalchemy_.ms_order_service.tenant import Tenant
from sqlalchemy_.ms_order_service.transaction import Transaction
sys.path.append(str(Path(__file__).resolve().parent.parent))
from flask_app.services.create_order import CreateOrder, kafka_out
from sqlalchemy_.ms_order_service.order import Order
from datetime import datetime

@patch('flask_app.services.create_order.logger')
def test_db_insert_order(mock_logger):
    create_order = CreateOrder()

    # Mock the session.add and session.commit methods
    create_order.session.add = MagicMock()
    create_order.session.commit = MagicMock()

    # Test when order creation is successful
    kwargs = {
        "tenant_id": "tenant1",
        "charge_point_id": "cp1",
        "connector_id": "con1",
        "id_tag": "tag1",
        "trigger_method": "start_charging",
        "request_id": "req1",
        "requires_payment": True
    }
    order = create_order.db_insert_order(**kwargs)
    assert isinstance(order, Order)
    assert order.tenant_id == "tenant1"
    assert order.charge_point_id == "cp1"
    assert order.connector_id == "con1"
    assert order.ev_driver_id == "tag1"
    assert order.is_charging == True
    assert order.is_reservation == False
    assert order.requires_payment == True
    assert order.request_id == "req1"

    # Test when order creation fails
    create_order.session.add.side_effect = Exception("Database error")
    result, status_code = create_order.db_insert_order(**kwargs)
    assert status_code == 500
    assert result["message"] == "insert order failed"
    assert result["action"] == "order_creation"
    mock_logger.error.assert_called_once_with("(X) Error while creating order: Database error")

@patch('flask_app.services.create_order.logger')
def test_db_insert_transaction(mock_logger):
    create_order = CreateOrder()

    # Mock the session.add and session.commit methods
    create_order.session.add = MagicMock()
    create_order.session.commit = MagicMock()

    # Test when transaction creation is successful
    transaction_id = "trans1"
    trans_det = "transaction detail"
    transaction = create_order.db_insert_transaction(transaction_id, trans_det)
    
    assert isinstance(transaction, Transaction)
    assert transaction.transaction_id == transaction_id
    assert transaction.transaction_detail == trans_det

    # Test when transaction creation fails
    create_order.session.add.side_effect = Exception("Database error")
    result, status_code = create_order.db_insert_transaction(transaction_id, trans_det)
    assert status_code == 500
    assert result["message"] == "insert transaction failed"
    assert result["action"] == "transaction_creation"

@patch('flask_app.services.create_order.DataValidation.validate_tenants', autospec=True)  
@patch('flask_app.services.create_order.logger')
@patch('flask_app.services.create_order.CreateOrder.db_insert_order', autospec=True)
@patch('flask_app.services.create_order.CreateOrder.db_insert_transaction', autospec=True)
@patch('flask_app.services.create_order.kafka_out', autospec=True)
def test_create_order(mock_kafka_out, mock_db_insert_transaction, mock_db_insert_order, mock_logger,mock_validate_tenants):
    create_order = CreateOrder()

    mock_validate_tenants.return_value = Tenant()

    # Mock the db_insert_order and db_insert_transaction methods
    mock_db_insert_order.return_value = Order()
    mock_db_insert_transaction.return_value = Transaction()

    # Mock the kafka_out method
    mock_kafka_out.return_value = None

    # Test when order and transaction creation is successful
    data = KafkaPayload()
    result = create_order.create_order(data)

    assert isinstance(result, dict)
    assert result['data']['transaction_id'] == Order().transaction_id
    assert result['data']['id_tag'] == data.id_tag
    assert result['data']['start_time'] == datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    assert result['data']['is_reservation'] == False
    assert result['data']['is_charging'] == False
    assert result['data']['tenant_id'] == data.tenant_id
    assert result['data']['status_code'] == 201
    mock_kafka_out.assert_called_once()

    # Test when order creation fails
    mock_db_insert_order.return_value = {"message": "insert order failed", "action":"order_creation","action_status":500,"status": 500}
    result = create_order.create_order(data)
    assert result["message"] == "insert order failed"
    assert result["action"] == "order_creation"
    assert result["action_status"] == 500
    assert result["status"] == 500
    
    # Test when transaction creation fails
    mock_db_insert_order.return_value = Order()
    mock_db_insert_transaction.return_value = {"message": "insert transaction failed", "action":"transaction_creation","action_status":500,"status": 500}
    result = create_order.create_order(data)
    assert result["message"] == "insert transaction failed"
    assert result["action"] == "transaction_creation"
    assert result["action_status"] == 500
    assert result["status"] == 500



