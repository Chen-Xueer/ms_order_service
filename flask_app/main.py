from flask_app.routes import ns_mobile as ns_mobile
from flask_app.routes import ns_kafka as ns_kafka
from microservice_utils.flask_init import flask_restx_init

app, api = flask_restx_init(
    title="Order Service API",
    version="1.0",
    description="Microservice API",
    swagger_doc="/swagger_doc",
)

api.add_namespace(ns_mobile, path="/")
api.add_namespace(ns_kafka, path="/")
