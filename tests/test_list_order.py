import pytest
from unittest.mock import ANY, Mock,MagicMock, patch
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from flask_app.services.models import KafkaPayload
from sqlalchemy import case, func
from sqlalchemy.sql.functions import coalesce
from sqlalchemy_.ms_order_service.transaction import Transaction
sys.path.append(str(Path(__file__).resolve().parent.parent))
from flask_app.services.update_order import UpdateOrder, kafka_out
from sqlalchemy_.ms_order_service.order import Order
from flask_app.services.list_order import ListOrder
from sqlalchemy_.ms_order_service.transaction import Transaction
from flask_app.services.common_function import DataValidation
from sqlalchemy_.ms_order_service.enum_types import OrderStatus, ReturnActionStatus, ReturnStatus,TriggerMethod
from ms_tools.kafka_management.topics import MsCSMSManagement,MsEVSEManagement,MsPaymentManagement,MsOrderManagement
from datetime import datetime

@patch('flask_app.services.list_order.DataValidation')
@patch('flask_app.services.list_order.Database')
def test_list_order_success(mock_database, mock_data_validation):
    # Arrange
    mock_session = Mock()
    mock_session.query = Mock()
    mock_database.return_value.init_session.return_value = mock_session
    mock_data_validation.return_value.validate_tenants.return_value = True
    mock_session.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
        (1, 'status', 'charge_point_id', 'connector_id', 'ev_driver_id', True, True, True, 'paid_by', None, None, 'duration', 'charged_energy', 'amount', 'transaction_detail')
    ]

    with patch('flask_app.services.common_function.DataValidation.validate_order', return_value=None) as mock_validate_order, \
         patch('flask_app.services.common_function.DataValidation.validate_order_request', return_value=None) as mock_validate_order_request, \
         patch('flask_app.services.create_order.CreateOrder.create_order_rfid', return_value=None) as mock_create_order_rfid:

        list_order = ListOrder()
        tenant_id = 'tenant_id'
        transaction_id = 'transaction_id'
        keyword = 'keyword'

        # Act
        result = list_order.list_order(tenant_id, transaction_id, keyword)

        # Assert
        mock_data_validation.return_value.validate_tenants.assert_called_once_with(tenant_id)
        mock_session.query.assert_called_once()
        mock_session.close.assert_called_once()
        assert result == {"data": []}

def test_list_order_failed():
    tenant_id = 'tenant_id'
    transaction_id = 'transaction_id'
    keyword = 'keyword'
    mock_session = Mock()
    mock_data_validation = Mock()
    mock_data_validation.validate_tenants.return_value = 'tenant_exists'
    mock_query = mock_session.query.return_value
    mock_query.outerjoin.return_value.filter.return_value.all.side_effect = Exception('Test exception')

    with patch('flask_app.services.common_function.DataValidation', return_value=mock_data_validation), \
         patch('flask_app.database_sessions.Database.init_session', return_value=mock_session):
        list_order_obj = ListOrder()
        result = list_order_obj.list_order(tenant_id, transaction_id, keyword)

        assert result == ({"status": ReturnStatus.ERROR.value, "message": "Internal server error"}, 500)


def test_list_transaction_summary_failed():
    tenant_id = 'tenant_id'

    with patch('flask_app.services.common_function.DataValidation.validate_tenants', return_value=None) as mock_validate_tenant:
        list_order = ListOrder()
        result = list_order.list_transaction_summary(tenant_id)
        
        assert result == ({'message': 'tenant_exists not found', 'action': 'order_retrieval', 'action_status': 'failed', 'status': 'error'}, 404)

def test_list_transaction_summary_success():
    tenant_id = 'tenant_id'
    mock_session = Mock()
    mock_data_validation = Mock()
    mock_data_validation.validate_tenants.return_value = 'tenant_exists'
    mock_query = mock_session.query.return_value
    mock_query.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = 'mock_summary'

    with patch('flask_app.services.common_function.DataValidation', return_value=mock_data_validation), \
         patch('flask_app.database_sessions.Database.init_session', return_value=mock_session):
        list_order_obj = ListOrder()
        result = list_order_obj.list_transaction_summary(tenant_id)

        mock_session.query.assert_called_with(
            Order.status,
            ANY,
            ANY
        )

        assert result == {"data": 'mock_summary'}

def test_list_transaction_breakdown_failed():
    tenant_id = 'tenant_id'

    with patch('flask_app.services.common_function.DataValidation.validate_tenants', return_value=None) as mock_validate_tenant:
        list_order = ListOrder()
        result = list_order.list_transaction_breakdown(tenant_id)
        assert result == ({'message': 'tenant_exists not found', 'action': 'order_retrieval', 'action_status': 'failed', 'status': 'error'}, 404)

def test_list_transaction_breakdown_success():
    tenant_id = 'tenant_id'
    mock_session = Mock()
    mock_data_validation = Mock()
    mock_data_validation.validate_tenants.return_value = 'tenant_exists'
    mock_query = mock_session.query.return_value
    mock_query.filter.return_value.group_by.return_value.all.return_value = 'mock_summary1'

    with patch('flask_app.services.common_function.DataValidation', return_value=mock_data_validation), \
         patch('flask_app.database_sessions.Database.init_session', return_value=mock_session):
        list_order_obj = ListOrder()
        result = list_order_obj.list_transaction_breakdown(tenant_id)

        mock_session.query.assert_called_with(
            ANY,
            ANY
        )

        assert result == {"data": 'mock_summary1'}