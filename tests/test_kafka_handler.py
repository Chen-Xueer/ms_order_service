from unittest.mock import MagicMock, patch
from kafka_app.handler import handler, validate_request
from kafka_app.kafka_management.kafka_topic import KafkaMessage


#@patch('kafka_app.handler.validate_request')
#@patch('flask_app.database_sessions.Database')
#def test_handler(mock_database, mock_validate_request):
#    # Arrange
#    mock_message = MagicMock(spec=KafkaMessage)
#    mock_message.topic = 'CREATE_ORDER'
#    mock_message.payload = {
#        "data": {
#            "trigger_method": "valid_trigger_method",
#            "transaction_id": 123,
#            "requires_payment": "valid_requires_payment",
#            "id_tag": "valid_id_tag",
#            "cognito_user_id": "valid_cognito_user_id"
#        },
#        "meta": {
#            "request_id": "valid_request_id"
#        }
#    }
#    mock_validate_request.return_value = (True, None)
#    mock_database_instance = mock_database.return_value
#    mock_session = mock_database_instance.init_session.return_value
#    # Act
#    handler(mock_message)
#    # Assert
#    mock_validate_request.assert_called_once_with(mock_message)
#    mock_database.assert_called_once()
#    mock_database_instance.init_session.assert_called_once()
#    mock_session.close.assert_called_once()


@patch('flask_app.services.common_function.DataValidation')
def test_validate_request(mock_data_validation):
    # Arrange
    mock_message = MagicMock(spec=KafkaMessage)
    mock_message.topic = "valid_topic"
    mock_message.payload = {
        "data": {
            "trigger_method": "valid_trigger_method",
            "transaction_id": 123,
            "requires_payment": "valid_requires_payment",
            "id_tag": "valid_id_tag",
            "cognito_user_id": "valid_cognito_user_id"
        },
        "meta": {
            "request_id": "valid_request_id"
        }
    }
    mock_data_validation().validate_null.return_value = {}
    mock_data_validation().validate_transaction_id.return_value = {}
    # Act
    result = validate_request(mock_message)
    # Assert
    assert result == (False, {"error_description": {"action": "Action Not Implemented"}, "status_code": 404})