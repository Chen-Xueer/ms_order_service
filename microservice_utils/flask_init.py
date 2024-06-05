import os
from flask import Flask, request
from flask.wrappers import Request
from flask_restx import Api, Resource, Namespace
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from typing import Any, Callable, Optional, Union, Literal, Tuple
from functools import wraps

from kafka_app.kafka_management.kafka_app import KafkaApp
from flask_app.database_sessions import Database

class Config(object):
    RESTX_MASK_SWAGGER = False
    SWAGGER_ENABLE = os.environ.get("SWAGGER_ENABLE", "TRUE")
    SWAGGER_UI_DOC_EXPANSION = 'list'
    JSON_SORT_KEYS = True # JSON sort keys
    DEBUG = True  # Enables/Disables debug mode
    TESTING = True  # Enables/Disables testing mode
    ERROR_404_HELP = True  # Disable automatic 404 help generation

def flask_restx_init(
    title: str = "Flask API",
    description: str = "Flask",
    version: str = "1.0",
    swagger_doc: Union[str, Literal[False]] = "/doc",
    kafka_app: Optional[KafkaApp] = None,
    token_validation: Optional[Callable[[Request, str], None]] = None,
) -> Tuple[Flask, Api, Callable[[Callable], Any]]:

    app = Flask(__name__)
    db = Database()

    #@app.before_request
    #def setup_session():
    #    db.init_session()  # get the session for the current thread

    @app.teardown_request
    def teardown_session(exception=None):
        if exception:
            db.rollback_session()  # rollback the transaction in case of error
        db.remove_session()  # remove the session for the current thread

    # Load configuration from Config class
    app.config.from_object(Config)

    # Initialize Flask-CORS
    CORS(app)

    # Initialize Flask-JWT-Extended
    JWTManager(app)

    # Swagger documentation
    if app.config["SWAGGER_ENABLE"] != "TRUE":
        swagger_doc = False

    api = Api(
        app=app,
        title=title,
        version=version,
        description=description,
        doc=swagger_doc,  # type: ignore
        authorizations={
            "Authorization": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
            }
        },
    )

    default_ns = Namespace("default", "Default APIs")

    @default_ns.route("/healthcheck", doc=False)
    class HealthCheck(Resource):
        def get(self):
            return {"healthcheck": "success"}, 200

    if kafka_app is not None:
        @default_ns.route("stop_application", doc=False)
        class StopApplication(Resource):
            def get(self):
                kafka_app.close()

                return {"message": "success"}, 200

    api.add_namespace(default_ns, path="/")

    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                if token_validation is not None:
                    token = request.headers.get("Authorization", None)
                    if token is None:
                        return {"message": "Authorization header missing"}, 401

                    token_validation(request, token)
                return f(*args, **kwargs)
            except Exception as e:
                return {"message": str(e)}, 401

        return decorated

    return app, api, token_required
