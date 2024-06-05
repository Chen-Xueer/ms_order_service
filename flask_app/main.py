from flask_app.routes import ns_mobile as ns_mobile
from flask_app.routes import ns_operator as ns_operator
from flask_app.routes import ns_kafka as ns_kafka
from microservice_utils.flask_init import flask_restx_init
from kafka_app.main import kafka_app

def token_validation(request, token: str) -> None:

    if token != "123":
        raise Exception("Token authorization failed")

    return None

app, api, token_required = flask_restx_init(
    title="Order Service API",
    description="Microservice API",
    version="1.0",
    swagger_doc="/swagger_doc",
    kafka_app=kafka_app,
    token_validation=token_validation,
)

api.add_namespace(ns_mobile, path="/orderservice/mobile/")
api.add_namespace(ns_operator, path="/orderservice/operator/")
api.add_namespace(ns_kafka, path="/orderservice/kafka/")
