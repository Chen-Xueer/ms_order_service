from functools import wraps
from kafka_app.kafka_management.kafka_topic import Topic
import os

topic = os.getenv('KAFKA_LOG_TOPIC')


def log_required(msg: str = "", headers: str = "", request_id: str = ""):

    def log_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            try:
                print(msg)
                from kafka_app.main import kafka_app
                kafka_app.send(
                    topic=Topic(
                        name=topic,
                        data=msg,
                        headers=headers
                    ),
                    request_id=request_id
                )

            except Exception as e:
                return {"error": str(e)}, 401

            return f(*args, **kwargs)

        return decorated

    return log_required
