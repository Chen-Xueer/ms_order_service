import os
from flask import Flask
from flask_restx import Api, Resource, Namespace
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from typing import Union, Literal, Tuple
from flask_app.database_sessions import Database

class Config(object):
    RESTX_MASK_SWAGGER = False
    AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
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
) -> Tuple[Flask, Api]:

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

    api.add_namespace(default_ns, path="/")

    return app, api
