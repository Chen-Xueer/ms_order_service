import pytest
from kafka_app.kafka_management.kafka_topic import Topic, KafkaMessage

def test_topic():
    # Arrange
    name = 'test_topic'
    data = {'key': 'value'}
    headers = {'header_key': 'header_value'}
    return_topic = 'return_topic'

    # Act
    topic = Topic(name, data, headers, return_topic)

    # Assert
    assert topic.name == name
    assert topic.data == data
    assert topic.headers == headers
    assert topic.return_topic == return_topic

def test_kafka_message():
    # Arrange
    topic = 'test_topic'
    headers = {'header_key': 'header_value'}
    payload = {'key': 'value'}
    key = 'test_key'

    # Act
    message = KafkaMessage(topic, headers, payload, key)

    # Assert
    assert message.topic == topic
    assert message.headers == headers
    assert message.payload == payload
    assert message.key == key