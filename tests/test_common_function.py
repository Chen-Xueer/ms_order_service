import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from sqlalchemy_.ms_order_service.tenant import Tenant
from flask_app.services.common_function import DataValidation

@pytest.fixture
def data_validation():
    with patch('flask_app.database_sessions.Database.init_session') as mock_init_session:
        mock_session = mock_init_session.return_value
        data_validation = DataValidation()
        yield data_validation
        data_validation = None

def test_validate_required_string(data_validation):
    assert data_validation.validate_required_string("", "test") == {"test": "test is required"}
    assert data_validation.validate_required_string(None, "test") == {"test": "test is required"}
    assert data_validation.validate_required_string("value", "test") == {}

def test_validate_required_integer(data_validation):
    assert data_validation.validate_required_integer(None, "test") == {"test": "test is required and must be integer"}
    assert data_validation.validate_required_integer("string", "test") == {"test": "test is required and must be integer"}
    assert data_validation.validate_required_integer(1, "test") == {}

def test_validate_required_boolean(data_validation):
    assert data_validation.validate_required_boolean(None, "test") == {"test": "test is required and must be boolean"}
    assert data_validation.validate_required_boolean("string", "test") == {"test": "test is required and must be boolean"}
    assert data_validation.validate_required_boolean(True, "test") == {}

def test_validate_required_list(data_validation):
    assert data_validation.validate_required_list(None, "test") == {"test": "test is required and must be list of valid charger types"}
    assert data_validation.validate_required_list("string", "test") == {"test": "test is required and must be list of valid charger types"}
    assert data_validation.validate_required_list(["value"], "test") == {}

def test_validate_required_date(data_validation):
    assert data_validation.validate_required_date(None, "test") == {"test": "test is required and must be date"}
    assert data_validation.validate_required_date(1, "test") == {"test": "test is required and must be date"}
    assert data_validation.validate_required_date("2021-01-01", "test") == {}

def test_validate_tenants():
    data_validation = DataValidation()
    # Mock the session.query method
    data_validation.session.query = MagicMock()
    # Test when tenant exists
    mock_tenant = Tenant()
    data_validation.session.query.return_value.filter.return_value.first.return_value = mock_tenant
    assert data_validation.validate_tenants("valid_tenant_id") == mock_tenant
    # Test when tenant does not exist
    data_validation.session.query.return_value.filter.return_value.first.return_value = None
    assert data_validation.validate_tenants("invalid_tenant_id") is None


def test_validate_order():
    data_validation = DataValidation()
    # Mock the session.query method
    data_validation.session.query = MagicMock()
    # Test when order exists
    data_validation.session.query.return_value.filter.return_value.first.return_value = MagicMock()
    assert data_validation.validate_order("valid_transaction_id") is not None
    # Test when order does not exist
    data_validation.session.query.return_value.filter.return_value.first.return_value = None
    assert data_validation.validate_order("invalid_transaction_id") is None


def test_validate_order_request():
    data_validation = DataValidation()
    # Mock the session.query method
    data_validation.session.query = MagicMock()
    # Test when order exists
    data_validation.session.query.return_value.filter.return_value.first.return_value = MagicMock()
    assert data_validation.validate_order_request("valid_request_id") is not None
    # Test when order does not exist
    data_validation.session.query.return_value.filter.return_value.first.return_value = None
    assert data_validation.validate_order_request("invalid_request_id") is None


def test_validate_transaction():
    data_validation = DataValidation()
    # Mock the session.query method
    data_validation.session.query = MagicMock()
    # Test when transaction exists
    data_validation.session.query.return_value.filter.return_value.first.return_value = MagicMock()
    assert data_validation.validate_transaction("valid_transaction_id") is not None
    # Test when transaction does not exist
    data_validation.session.query.return_value.filter.return_value.first.return_value = None
    assert data_validation.validate_transaction("invalid_transaction_id") is None

