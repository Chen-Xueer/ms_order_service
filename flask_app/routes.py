from flask import request
from flask_restx import Namespace, Resource
from flask_app.swagger_models import RequestModel,ResponseModel
from flask_app.services.create_order import CreateOrder
from flask_app.auth import token_required,decode_token
from microservice_utils.settings import logger
import uuid


ns_mobile = Namespace("orderservice/mobile", "APIs related to operator")
request_model = RequestModel(ns_mobile)
response_model = ResponseModel(ns_mobile)


# PATH: /orderservice/mobile/order
@ns_mobile.route("/order/<string:mobile_id>")
class order(Resource):
    #@ns_mobile.doc(security="Authorization")
    #@token_required
    @ns_mobile.expect(request_model.create_order(), validate=True)
    @ns_mobile.marshal_with(response_model.create_order(), skip_none=True)
    def post(self,mobile_id):
        #token = str(request.headers["Authorization"])
        #claims = decode_token(token)
        tenant = 'TenantA'

        data = request.json

        create_order = CreateOrder()
        return create_order.create_order_mobile_id(mobile_id=mobile_id,data=data,tenant=tenant)
    

