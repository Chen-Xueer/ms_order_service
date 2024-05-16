from flask_app.routes import ns_mobile as ns_mobile
from microservice_utils.flask_init import flask_restx_init

app, api = flask_restx_init(
    title="MS_ORDER_SERVICE API",
    version="1.0",
    description="Microservice API",
    swagger_doc="/swagger",
)

api.add_namespace(ns_mobile, path="/")
