import pytest
from unittest.mock import ANY, Mock,MagicMock, patch
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from flask_app.services.models import KafkaPayload
from sqlalchemy import case, func
from sqlalchemy.sql.functions import coalesce
from sqlalchemy_.ms_order_service.tenant import Tenant
from sqlalchemy_.ms_order_service.transaction import Transaction
sys.path.append(str(Path(__file__).resolve().parent.parent))
from flask_app.services.update_order import UpdateOrder, kafka_out
from sqlalchemy_.ms_order_service.order import Order
from flask_app.services.list_order import ListOrder
from sqlalchemy_.ms_order_service.transaction import Transaction
from flask_app.services.common_function import DataValidation
from sqlalchemy_.ms_order_service.enum_types import OrderStatus, ReturnActionStatus, ReturnStatus,TriggerMethod
from kafka_app.kafka_management.topic_enum import MsCSMSManagement,MsEVSEManagement,MsPaymentManagement,MsOrderManagement
from datetime import datetime

@patch('flask_app.services.list_order.DataValidation')
@patch('flask_app.services.list_order.Database')
def test_list_order_success(mock_database, mock_data_validation):
    # Arrange
    mock_session = Mock()
    mock_session.query = Mock()
    mock_database.return_value.init_session.return_value = mock_session
    mock_data_validation.return_value.validate_tenants.return_value = Tenant()
    mock_session.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
        (1, 'status', 'charge_point_id', 'connector_id', 'ev_driver_id', True, True, True, 'paid_by', None, None, 'duration', 'charged_energy', 'amount', 'transaction_detail')
    ]

    list_order = ListOrder()
    tenant_id = 'tenant_id'
    transaction_id = 'transaction_id'
    keyword = 'keyword'
    # Act
    result = list_order.list_order(tenant_id, transaction_id, keyword)
    # Assert
    mock_data_validation.return_value.validate_tenants.assert_called_once_with(tenant_id='tenant_id', action='order_retrieval')
    mock_session.query.assert_called_once()
    mock_session.close.assert_called_once()
    assert result == {"data": []}


def test_list_order_failed():
    tenant_id = 'tenant_id'
    transaction_id = 'transaction_id'
    keyword = 'keyword'

    with patch('flask_app.services.common_function.DataValidation.validate_tenants', return_value=({'message': 'tenant_exists not found', 'action': 'order_retrieval', 'action_status': 'failed', 'status': 'error'}, 404)) as mock_validate_tenant:
        list_order_obj = ListOrder()
        result = list_order_obj.list_order(tenant_id, transaction_id, keyword)

        assert result == ({'message': 'tenant_exists not found', 'action': 'order_retrieval', 'action_status': 'failed', 'status': 'error'}, 404)


@patch('flask_app.services.list_order.DataValidation')
@patch('flask_app.services.list_order.Database')
def test_list_transaction_summary_success(mock_database, mock_data_validation):
    # Arrange
    mock_session = Mock()
    mock_session.query = Mock()
    mock_database.return_value.init_session.return_value = mock_session
    mock_session.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = [
        ('Available', '12', '777')
    ]

    mock_data_validation.return_value.validate_tenants.return_value = Tenant()

    list_order = ListOrder()
    tenant_id = 'tenant_id'
    # Act
    result = list_order.list_transaction_summary(tenant_id)
    # Assert
    mock_data_validation.return_value.validate_tenants.assert_called_once_with(tenant_id='tenant_id', action='transaction_summary_retrieval')
    mock_session.query.assert_called_once()
    assert result == {
        "data": [('Available', '12', '777')]
    }


def test_list_transaction_summary_failed():
    tenant_id = 'tenant_id'

    with patch('flask_app.services.common_function.DataValidation.validate_tenants', return_value=({'message': 'tenant_exists not found', 'action': 'order_retrieval', 'action_status': 'failed', 'status': 'error'}, 404)) as mock_validate_tenant:
        list_order = ListOrder()
        result = list_order.list_transaction_summary(tenant_id)
        
        assert result == ({'message': 'tenant_exists not found', 'action': 'order_retrieval', 'action_status': 'failed', 'status': 'error'}, 404)

def test_list_transaction_breakdown_failed():
    tenant_id = 'tenant_id'

    with patch('flask_app.services.common_function.DataValidation.validate_tenants', return_value=({'message': 'tenant_exists not found', 'action': 'order_retrieval', 'action_status': 'failed', 'status': 'error'}, 404)) as mock_validate_tenant:
        list_order = ListOrder()
        result = list_order.list_transaction_breakdown(tenant_id)
        assert result == ({'message': 'tenant_exists not found', 'action': 'order_retrieval', 'action_status': 'failed', 'status': 'error'}, 404)

@patch('flask_app.services.list_order.DataValidation')
@patch('flask_app.services.list_order.Database')
def test_list_transaction_breakdown_success(mock_database, mock_data_validation):
    # Arrange
    mock_session = Mock()
    mock_session.query = Mock()
    mock_database.return_value.init_session.return_value = mock_session
    mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
        ('Available', '12')
    ]

    mock_data_validation.return_value.validate_tenants.return_value = Tenant()

    list_order = ListOrder()
    tenant_id = 'tenant_id'
    # Act
    result = list_order.list_transaction_breakdown(tenant_id)
    # Assert
    mock_data_validation.return_value.validate_tenants.assert_called_once_with(tenant_id='tenant_id', action='transaction_breakdown_retrieval')
    mock_session.query.assert_called_once()
    assert result == {
        "data": [('Available', '12')]
    }